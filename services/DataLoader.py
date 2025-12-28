import json
import time
from csv import DictReader
from typing import List, Dict

import requests

from services import normalize_date, parse_amount


class DataLoader:
    def __init__(self, configs):
        self.configs = configs

    def load_data(self, csv_reader: DictReader, asset_name: str, group_title: str):
        deposits, withdrawals = self.read_csv(csv_reader, asset_name=asset_name)
        print(f"Prepared {len(deposits + withdrawals)} transactions from csv")

        # send in batches
        succeeded = 0
        failed = 0
        for i in range(0, len(deposits), self.configs["app"]["batch_size"]):
            batch = deposits[i:i + self.configs["app"]["batch_size"]]
            try:
                res = self.post_transactions_batch(batch, group_title=group_title)
                # The API returns created objects — you can inspect them
                print(f"Batch {i // self.configs["app"]["batch_size"] + 1}: posted {len(batch)} txs and received {len(res)} responses.")
                succeeded += len(batch)
                # be polite
                time.sleep(0.5)
            except Exception as e:
                print("Batch failed:", e)
                failed += len(batch)
                # continue with next batch
                time.sleep(1)
        
        for i in range(0, len(withdrawals), self.configs["app"]["batch_size"]):
            batch = withdrawals[i:i + self.configs["app"]["batch_size"]]
            try:
                res = self.post_transactions_batch(batch, group_title=group_title)
                # The API returns created objects — you can inspect them
                print(f"Batch {i // self.configs["app"]["batch_size"] + 1}: posted {len(batch)} txs and received {len(res)} responses.")
                succeeded += len(batch)
                # be polite
                time.sleep(0.5)
            except Exception as e:
                print("Batch failed:", e)
                failed += len(batch)
                # continue with next batch
                time.sleep(1)

        print(f"Done. succeeded={succeeded} failed={failed}")

    def post_transactions_batch(self, txs_batch: List[Dict], group_title: str) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.configs["firefly"]["token"]}",
            # Firefly expects this Accept header in some versions to avoid HTML redirects.
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/json",
        }
        payload = {
            "apply_rules": self.configs["app"]["apply_rules"],
            "transactions": txs_batch,
            "group_title": group_title
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

    def read_csv(self, csv_reader: DictReader, asset_name: str):
        deposits = []
        withdrawals = []
        for row in csv_reader:
            # try common header names
            # adapt these arrays if your CSV uses other headers
            row_lower = {k.lower().strip(): v for k, v in row.items()}

            date_raw = row_lower.get("date") or row_lower.get("transaction date") or row_lower.get("txn date") or row_lower.get("posted date") or ""
            amount_raw = row_lower.get("amount") or row_lower.get("amt") or ""
            desc_raw = row_lower.get("description") or row_lower.get("details") or row_lower.get("narration") or row_lower.get("merchant") or ""
            date = normalize_date(date_raw) if date_raw else None
            amount, txn_type = parse_amount(amount_raw)
            description = desc_raw.strip() if desc_raw else "(no description)"

            # Build transaction object - use withdrawal so credit card is the source
            if txn_type == "deposit":
                deposits.append({
                    "date": date,  # YYYY-MM-DD
                    "description": description[:255],
                    "type": txn_type,
                    "amount": amount,  # positive decimal string
                    "currency": self.configs["app"]["currency"],
                    # IMPORTANT: use source_name so Firefly links to existing account by name.
                    "source_name": "UPI" if description[:100].startswith("PAYMENT RECEIVED. THANK YOU") else description[:100],
                    # destination_name will become the income account in Firefly
                    "destination_name": asset_name,
                    "category_name": row_lower.get("category") or "",
                    "external_id": row_lower.get("reference") or ""
                })
            if txn_type == "withdrawal":
                withdrawals.append({
                    "date": date,  # YYYY-MM-DD
                    "description": description[:255],
                    "type": txn_type,
                    "amount": amount,  # positive decimal string
                    "currency": self.configs["app"]["currency"],
                    # IMPORTANT: use source_name so Firefly links to existing account by name.
                    "source_name": asset_name,
                    # destination_name will become the expense account/merchant in Firefly
                    "destination_name": description[:100],
                    "category_name": row_lower.get("category") or "",
                    "external_id": row_lower.get("reference") or ""
                })
        return deposits, withdrawals
