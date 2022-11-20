import asyncio
import threading
from threading import Thread

from subalert.base import Utils
from subalert.logger import log_events
from subalert.extrinsic_parser import ParseExtrinsic
from substrateinterface import ExtrinsicReceipt

from .config import Configuration
from .subq import Queue

queue = Queue()
utils = Utils()
log = log_events(filename='extrinsic-monitor.log', debug=False)


class ExtrinsicMonitor:
    def __init__(self):
        self.previous_block_hash = []
        self.sema = threading.Semaphore(value=10)
        self.config = Configuration()
        self.substrate = self.config.substrate

        # Queue events
        self.loop = asyncio.get_event_loop()

    def inspect_extrinsic(self, block, extrinsic_types, check_receipt):
        self.sema.acquire()
        result = self.substrate.get_block(block_number=block, ignore_decoding_errors=True)
        block_hash, extrinsics_list = result['header']['hash'], []

        for extrinsic in result['extrinsics']:
            extrinsic_hash = extrinsic.value['extrinsic_hash']

            if extrinsic_hash is None:
                continue

            if extrinsic['call']['call_function']['name'] in extrinsic_types:
                log.info(f"Checking if extrinsic: {extrinsic_hash} has been signed")
                if check_receipt:
                    extrinsic_receipt = ExtrinsicReceipt(
                        substrate=self.substrate,
                        extrinsic_hash=extrinsic_hash,
                        block_hash=block_hash)

                    if extrinsic_receipt.is_success is not True:
                        log.warning("extrinsic is not successful")
                        continue

                    extrinsics_list.append(extrinsic.value)
        log.info(f"{len(extrinsics_list)} extrinsic(s) were successfully signed on block {block}")
        self.process_extrinsics(extrinsics=extrinsics_list)
        self.sema.release()
        return block_hash, extrinsics_list

    def process_extrinsics(self, extrinsics):
        block_event_construct = {"transactions": [], 'batch_all': []}

        # Pass all successful extrinsics to the appropriate function for parsing.
        # file: extrinsic_parser.py
        for extrinsic in extrinsics:
            if extrinsic is not None:
                call_type = extrinsic['call']['call_function']
                extrinsic_data = ParseExtrinsic(extrinsic)

                if call_type == 'transfer':
                    transaction = extrinsic_data.transactions
                    block_event_construct['transactions'].append(transaction)

                elif call_type == 'batch_all':
                    batch_all = extrinsic_data.remark_batch_all
                    if batch_all:
                        block_event_construct['batch_all'].append(batch_all)

        queue.enqueue(block_event_construct)

        # Run queue task if size is >= 1, clear queue & block_event_construct once complete.
        if queue.size() >= 1:
            task = self.loop.create_task(queue.process_queue())
            self.loop.run_until_complete(task)

        queue.clear()
        block_event_construct.clear()

    def new_block(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from subscribe_block_headers()
        :param update_nr: passed from subscribe_block_headers()
        :param subscription_id: passed from subscribe_block_headers()
        :return: When a new block occurs, it is checked against check_transaction to see if the amount transacted is
                 greater than the threshold set.
        """
        block = obj['header']['number'] - 20  # 25 blocks behind
        parent_block_hash = obj['header']['parentHash']
        calls = ['batch_all', 'remark', 'transfer']

        # check current hash and previous hash to mitigate
        # duplicate blocks whilst subscribed
        if parent_block_hash not in self.previous_block_hash:
            if len(self.previous_block_hash) >= 1:
                self.previous_block_hash.pop(len(self.previous_block_hash) - 1)
            self.previous_block_hash.append(parent_block_hash)

            log.info("")
            log.info(f"🔨 New block: {block} produced by: {obj['author']}")
            thread = Thread(target=self.inspect_extrinsic, daemon=True, args=(block, calls, True,))

            thread.start()
            thread.join()
        else:
            pass
