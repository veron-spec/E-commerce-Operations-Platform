# API Documentation

Base URL: `http://localhost:8000/api/v1`

## Health Check

`GET /health` → `{"status": "ok"}`

## Stores

### List Stores
```
GET /api/v1/stores
```

### Add Store
```
POST /api/v1/stores
Params: name, platform_type, store_url, api_key, api_secret
```

### Trigger Sync
```
GET /api/v1/stores/{id}/sync
```

## Dashboard

### Summary
```
GET /api/v1/dashboard/summary?days=30&store_id=1
```

## Analytics

### Sales Analysis
```
GET /api/v1/analytics/sales?days=30&granularity=day&store_id=1
```

### Inventory Analysis
```
GET /api/v1/analytics/inventory?store_id=1&low_stock_threshold=10
```

### Trend Analysis
```
GET /api/v1/analytics/trends?days=60&store_id=1
```

### Top Products
```
GET /api/v1/analytics/products/top?days=30&limit=10&store_id=1
```
