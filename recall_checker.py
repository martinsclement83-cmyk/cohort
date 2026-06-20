# recall_checker.py


import requests


class RecallChecker:
    """
    Checks whether a medication appears in FDA recall notices.
    """

    BASE_URL = "https://api.fda.gov/drug/enforcement.json"

    def check_recall(self, drug_name):
        """
        Returns recall information if found.

        Args:
            drug_name (str): medication name

        Returns:
            dict | None
        """

        try:
            query = (
                f'{self.BASE_URL}?search=product_description:"{drug_name}"'
                '&limit=1'
            )

            response = requests.get(query, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "results" not in data:
                return None

            recall = data["results"][0]

            return {
                "status": recall.get("status", "Unknown"),
                "reason": recall.get(
                    "reason_for_recall",
                    "Reason not available"
                ),
                "classification": recall.get(
                    "classification",
                    "Unknown"
                ),
                "recall_date": recall.get(
                    "recall_initiation_date",
                    "Unknown"
                )
            }

        except requests.exceptions.RequestException:
            return None

        except Exception:
            return None
