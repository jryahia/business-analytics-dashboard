# Business Analytics Dashboard

**Self-hosted analytics dashboard: KPIs, drag-and-drop dashboards, dataset upload, AI insights and PDF/Excel export, with a desktop companion app.**

![Python](https://img.shields.io/badge/Python-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![FastAPI](https://img.shields.io/badge/FastAPI-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![React](https://img.shields.io/badge/React-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![TypeScript](https://img.shields.io/badge/TypeScript-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![Celery](https://img.shields.io/badge/Celery-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![Redis](https://img.shields.io/badge/Redis-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-161b22?style=for-the-badge&labelColor=161b22&color=161b22) ![Flet](https://img.shields.io/badge/Flet-161b22?style=for-the-badge&labelColor=161b22&color=161b22)

```mermaid
flowchart LR
    S0["Dataset upload (CSV / Excel)"]
    S1["FastAPI + Celery workers"]
    S2["KPI + insight engine"]
    S3["React dashboards (SSE)"]
    S4["PDF / Excel export"]
    S0 --> S1 --> S2 --> S3 --> S4
```

## Problem it solves

Small teams pay for BI tools they barely use, or keep KPIs in spreadsheets. This dashboard runs on their own server, ingests datasets, tracks KPIs live and exports reports.

A comprehensive business intelligence dashboard with FastAPI backend, React/TypeScript frontend, and a Flet desktop companion app. Features real-time analytics, interactive KPI tracking, data filtering, report export, and Docker Compose deployment.

## Features
- Real-time analytics
- Interactive dashboards
- Data export
- Docker deployment
- Flet desktop app

## Tech Stack
Python, FastAPI, React, TypeScript, Docker