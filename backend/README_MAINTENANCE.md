# Improving NLP: Data Collection & Retraining

1. **Collect more labeled data:**
   - Create a CSV file named `nlp_corpus.csv` in the `backend` folder.
   - Format: two columns, `text` and `label` (label = positive, negative, or neutral).
   - Example:
     text,label
     "Steel prices expected to rise due to demand surge",negative
     "Cement supply stable, prices steady",neutral
     "Fuel price drop may lower transport costs",positive

2. **Retrain the NLP model:**
   - Run:
     ```bash
     python backend/train_nlp.py
     ```
   - This will use your new `nlp_corpus.csv` for training and save an improved model.

# Automating Live Data Ingestion & Retraining

1. **Windows Task Scheduler:**
   - Open Task Scheduler > Create Task.
   - Set trigger (e.g., daily at 6am).
   - Action: Start a program
     - Program/script: python
     - Add arguments: backend/ingest_live.py
     - Start in: (your project folder)
   - Repeat for `backend/train_models.py` and `backend/train_nlp.py` if you want regular retraining.

2. **On Linux/macOS (cron):**
   - Edit your crontab:
     ```bash
     crontab -e
     ```
   - Add lines like:
     0 6 * * * cd /path/to/project/backend && python ingest_live.py
     30 6 * * * cd /path/to/project/backend && python train_models.py
     45 6 * * * cd /path/to/project/backend && python train_nlp.py

This keeps your live features and models up-to-date automatically.
