---
topic: lotofacil-prediction-webapp
---

# Lotofacil Number Prediction Webapp

## Problem Frame

A 22-year historical dataset of Lotofácil draws (3,656 entries, 15 numbers from 1–25 per draw)
exists in `data.json`. The goal is to build a multi-service webapp that performs deep statistical
and ML analysis on this data, correlates it with external world signals, and generates
self-consistent "scenario path" of predicted future draws.

The system serves two simultaneous purposes: rigorous pattern-research (including PI alignment,
event correlation, order analysis) and actionable number suggestions for real play.
All predictions must carry explicit confidence scores — no false certainty.

Ideas of similarity occurrencies to sustains and correlations events to help in the predicting process:
Try to find a world signal thats occur in the same patterns, it would consider world events, signals, market changes and patterns, earth position.
historical events that matchs with the market changes, or other events that affected in to the relation.

---

## Requirements

**Data & Ingestion**
- R1. The system must ingest `data.json` as its primary data source (3,656 draws, DD-MM-YYYY dates, 15 numbers per draw from 1–25).