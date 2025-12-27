import json
import time
from csv import DictReader
from typing import List, Dict

import requests

from services import normalize_date, parse_amount


class DataLoader:
    def __init__(self, configs):
        self.configs = configs

    def load_data(self, csv_reader: DictReader, asset_name: str):
        all_txs = self.read_csv(csv_reader)
        print(f"Prepared {len(all_txs)} transactions from csv")

        # send in batches
        succeeded = 0
        failed = 0
        for i in range(0, len(all_txs), self.configs["app"]["batch_size"]):
            batch = all_txs[i:i + self.configs["app"]["batch_size"]]
            try:
                res = self.post_transactions_batch(batch)
                # The API returns created objects — you can inspect them
                print(f"Batch {i // self.configs["app"]["batch_size"] + 1}: posted {len(batch)} txs.")
                succeeded += len(batch)
                # be polite
                time.sleep(0.5)
            except Exception as e:
                print("Batch failed:", e)
                failed += len(batch)
                # continue with next batch
                time.sleep(1)

        print(f"Done. succeeded={succeeded} failed={failed}")

    def post_transactions_batch(self, txs_batch: List[Dict]) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.configs["firefly"]["token"]}",
            # Firefly expects this Accept header in some versions to avoid HTML redirects.
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/json",
        }
        payload = {
            "apply_rules": self.configs["app"]["apply_rules"],
            "transactions": txs_batch
        }
        r = requests.post(f"{self.configs["firefly"]["base_url"]}/api/v1/transactions",
                          headers=headers,
                          data=json.dumps(payload),
                          timeout=30)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            print("HTTP error:", r.status_code, r.text)
            raise
        return r.json()

    def read_csv(self, csv_reader: DictReader, asset_name: str) -> List[Dict]:
        txs = []
        headers = [h.lower().strip() for h in csv_reader.fieldnames]
        for row in csv_reader:
            # try common header names
            # adapt these arrays if your CSV uses other headers
            date_raw = row.get("date") or row.get("transaction date") or row.get("txn date") or row.get("posted date") or ""
            amount_raw = row.get("amount") or row.get("amt") or ""
            desc_raw = row.get("description") or row.get("details") or row.get("narration") or row.get("merchant") or ""

            date = normalize_date(date_raw) if date_raw else None
            amount = parse_amount(amount_raw)
            txn_type = "deposit" if float(amount) < 0 else "withdrawal"  # expense from CC
            description = desc_raw.strip() if desc_raw else "(no description)"

            # Build transaction object - use withdrawal so credit card is the source
            tx = {
                "date": date,  # YYYY-MM-DD
                "description": description[:255],
                "type": txn_type,
                "amount": amount,  # positive decimal string
                "currency": self.configs["app"]["currency"],
                # IMPORTANT: use source_name so Firefly links to existing account by name.
                "source_name": asset_name,
                # destination_name will become the expense account/merchant in Firefly
                "destination_name": description[:100],
            }
            txs.append(tx)
        return txs
