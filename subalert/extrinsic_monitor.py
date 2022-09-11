import asyncio
import urllib.parse
import urllib.request

from colorama import Fore, Style
from subalert.base import Numbers, Utils, SubQuery, CoinGecko, Public_API
from subalert.logger import log_events
from substrateinterface import ExtrinsicReceipt
from subalert.extrinsic_parser import ParseExtrinsic
from .config import Configuration
from .subq import Queue

queue = Queue()
utils = Utils()
log = log_events(filename='extrinsic-monitor.log', debug=False)


class ExtrinsicMonitor:
    def __init__(self):
        self.previous_hash = []
        self.config = Configuration()
        self.substrate = self.config.substrate

        # Queue events
        self.loop = asyncio.get_event_loop()

    def extrinsic(self, block, extrinsic_types, check_receipt):
        result = self.substrate.get_block(block_number=block, ignore_decoding_errors=True)
        block_hash, extrinsics_list = result['header']['hash'], []

        for extrinsic in result['extrinsics']:
            extrinsic_hash = extrinsic.value['extrinsic_hash']

            if extrinsic_hash is None:
                continue

            if extrinsic['call']['call_function']['name'] in extrinsic_types:
                if check_receipt:
                    extrinsic_receipt = ExtrinsicReceipt(
                        substrate=self.substrate,
                        extrinsic_hash=extrinsic_hash,
                        block_hash=block_hash)

                    if extrinsic_receipt.is_success is not True:
                        log.warning("extrinsic is not successful")
                        continue

                    extrinsics_list.append(extrinsic.value)

        self.substrate.websocket.ping()
        return block_hash, extrinsics_list

    def new_block(self, obj, update_nr, subscription_id):
        """
        :param obj: passed from subscribe_block_headers()
        :param update_nr: passed from subscribe_block_headers()
        :param subscription_id: passed from subscribe_block_headers()
        :return: When a new block occurs, it is checked against check_transaction to see if the amount transacted is
                 greater than the threshold set.
        """
        block = obj['header']['number'] - 50  # 50 blocks behind
        bhash = obj['header']['parentHash']

        block_event_construct = {"transactions": [], 'batch_all': []}
        calls = ['batch_all', 'remark', 'transfer']

        # check current hash and previous hash to mitigate
        # duplicate blocks whilst subscribed
        if bhash not in self.previous_hash:
            if len(self.previous_hash) >= 1:
                self.previous_hash.pop(len(self.previous_hash) - 1)
            self.previous_hash.append(bhash)

            blockhash, extrinsics = self.extrinsic(block=block, extrinsic_types=calls, check_receipt=True)

            print(f"{Style.DIM}🔨 New block: {Style.RESET_ALL}{Style.BRIGHT}{block}{Style.RESET_ALL} {Style.DIM}produced by: {Style.RESET_ALL}{Style.BRIGHT}{obj['author']}{Style.RESET_ALL}")
            print(f"{Style.DIM}Monitored extrinsics found in block: {Style.RESET_ALL}{Fore.LIGHTGREEN_EX}{len(extrinsics)}{Style.RESET_ALL}\n")

            for extrinsic in extrinsics:
                if extrinsic is not None:
                    call_type = extrinsic['call']['call_function']
                    extrinsic_data = ParseExtrinsic(extrinsic)

                    if call_type == 'transfer':
                        transaction = extrinsic_data.transactions
                        block_event_construct['transactions'].append(transaction)

                    elif call_type == 'batch_all':
                        batch_all = extrinsic_data.remark_batch_all
                        block_event_construct['batch_all'].append(batch_all)

            queue.enqueue(block_event_construct)

            # Run queue task if size is >= 1, clear queue & block_event_construct once complete.
            if queue.size() >= 1:
                task = self.loop.create_task(queue.process_queue())
                self.loop.run_until_complete(task)

            queue.clear()
            block_event_construct.clear()

        else:
            pass
