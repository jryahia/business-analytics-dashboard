import requests
from typing import Any, Dict, List, Optional


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})
        self.timeout = 10

    def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError:
            raise APIError("Cannot connect to backend. Is it running on localhost:8000?")
        except requests.Timeout:
            raise APIError("Request timed out")
        except requests.HTTPError:
            raise APIError(f"HTTP {response.status_code}: {response.text}", response.status_code)
        except Exception as e:
            raise APIError(str(e))

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict) -> Any:
        return self._request("POST", endpoint, json=data)

    def put(self, endpoint: str, data: Dict) -> Any:
        return self._request("PUT", endpoint, json=data)

    def delete(self, endpoint: str) -> Any:
        return self._request("DELETE", endpoint)

    def is_reachable(self) -> bool:
        try:
            self.get("/health")
            return True
        except APIError:
            return False

    # KPIs
    def get_kpis(self) -> List[Dict]:
        return self.get("/api/kpis")

    # Datasets
    def get_datasets(self) -> List[Dict]:
        return self.get("/api/datasets")

    def get_dataset(self, dataset_id: str) -> Dict:
        return self.get(f"/api/datasets/{dataset_id}")

    def create_dataset(self, data: Dict) -> Dict:
        return self.post("/api/datasets", data)

    def delete_dataset(self, dataset_id: str) -> Dict:
        return self.delete(f"/api/datasets/{dataset_id}")

    def export_dataset(self, dataset_id: str, fmt: str = "csv") -> bytes:
        url = f"{self.base_url}/api/datasets/{dataset_id}/export"
        try:
            r = self.session.get(url, params={"format": fmt}, timeout=30)
            r.raise_for_status()
            return r.content
        except Exception as e:
            raise APIError(str(e))

    # Data Sources
    def get_sources(self) -> List[Dict]:
        return self.get("/api/sources")

    def create_source(self, data: Dict) -> Dict:
        return self.post("/api/sources", data)

    def test_source(self, source_id: str) -> Dict:
        return self.post(f"/api/sources/{source_id}/test", {})

    def delete_source(self, source_id: str) -> Dict:
        return self.delete(f"/api/sources/{source_id}")

    # Charts
    def get_charts(self) -> List[Dict]:
        return self.get("/api/charts")

    def get_chart_data(self, chart_id: str) -> Dict:
        return self.get(f"/api/charts/{chart_id}/data")

    def create_chart(self, data: Dict) -> Dict:
        return self.post("/api/charts", data)

    def delete_chart(self, chart_id: str) -> Dict:
        return self.delete(f"/api/charts/{chart_id}")

    # Analytics
    def get_analytics(self, metric: str, period: str = "30d") -> Dict:
        return self.get(f"/api/analytics/{metric}", params={"period": period})

    # Mock fallback data used when backend is unavailable
    def get_mock_kpis(self) -> List[Dict]:
        return [
            {"id": "1", "title": "Total Revenue", "value": "$124,563", "change": 12.5, "trend": "up", "icon": "attach_money"},
            {"id": "2", "title": "Active Users", "value": "8,429", "change": 8.2, "trend": "up", "icon": "people"},
            {"id": "3", "title": "Conversion Rate", "value": "3.24%", "change": -1.8, "trend": "down", "icon": "trending_up"},
            {"id": "4", "title": "Avg. Order Value", "value": "$68.50", "change": 5.1, "trend": "up", "icon": "shopping_cart"},
        ]

    def get_mock_datasets(self) -> List[Dict]:
        return [
            {"id": "1", "name": "Sales Q1 2025", "rows": 15420, "columns": 12, "source": "PostgreSQL", "updated": "2025-04-01", "status": "active"},
            {"id": "2", "name": "Customer Segments", "rows": 8930, "columns": 8, "source": "CSV Upload", "updated": "2025-04-15", "status": "active"},
            {"id": "3", "name": "Product Inventory", "rows": 3240, "columns": 15, "source": "MySQL", "updated": "2025-03-28", "status": "syncing"},
            {"id": "4", "name": "Marketing Campaigns", "rows": 1205, "columns": 20, "source": "API", "updated": "2025-04-20", "status": "active"},
            {"id": "5", "name": "User Behavior Logs", "rows": 98432, "columns": 6, "source": "BigQuery", "updated": "2025-04-22", "status": "error"},
        ]

    def get_mock_sources(self) -> List[Dict]:
        return [
            {"id": "1", "name": "Production DB", "type": "postgresql", "host": "prod.db.internal", "status": "connected", "last_sync": "2 min ago"},
            {"id": "2", "name": "Analytics MySQL", "type": "mysql", "host": "analytics.mysql.internal", "status": "connected", "last_sync": "5 min ago"},
            {"id": "3", "name": "Data Warehouse", "type": "bigquery", "host": "bigquery.googleapis.com", "status": "connected", "last_sync": "1 hour ago"},
            {"id": "4", "name": "Legacy Oracle", "type": "oracle", "host": "legacy.oracle.internal", "status": "error", "last_sync": "3 days ago"},
        ]

    def get_mock_charts(self) -> List[Dict]:
        return [
            {"id": "1", "title": "Revenue Over Time", "type": "line", "dataset": "Sales Q1 2025", "created": "2025-04-01"},
            {"id": "2", "title": "Sales by Category", "type": "bar", "dataset": "Sales Q1 2025", "created": "2025-04-05"},
            {"id": "3", "title": "Customer Distribution", "type": "pie", "dataset": "Customer Segments", "created": "2025-04-10"},
        ]

    def get_mock_revenue_series(self) -> List[Dict]:
        return [
            {"month": "Jan", "value": 42000},
            {"month": "Feb", "value": 58000},
            {"month": "Mar", "value": 51000},
            {"month": "Apr", "value": 67000},
            {"month": "May", "value": 73000},
            {"month": "Jun", "value": 69000},
            {"month": "Jul", "value": 84000},
            {"month": "Aug", "value": 91000},
            {"month": "Sep", "value": 88000},
            {"month": "Oct", "value": 96000},
            {"month": "Nov", "value": 112000},
            {"month": "Dec", "value": 124563},
        ]

    def get_mock_category_sales(self) -> List[Dict]:
        return [
            {"category": "Electronics", "value": 45},
            {"category": "Clothing", "value": 28},
            {"category": "Home & Garden", "value": 18},
            {"category": "Sports", "value": 9},
        ]
