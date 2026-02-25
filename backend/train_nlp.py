import os
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from joblib import dump

DATA_CSV = os.path.join(os.path.dirname(__file__), '..', 'davaobuild_dataset_2025_2026.csv')
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

def load_corpus():
    # Prefer a dedicated corpus file if present
    corpus_path = os.path.join(os.path.dirname(__file__), 'nlp_corpus.csv')
    if os.path.exists(corpus_path):
        df = pd.read_csv(corpus_path)
        if 'text' in df.columns and 'label' in df.columns:
            return df[['text','label']]
    # fallback: build tiny synthetic dataset from notes or defaults
    df_all = pd.read_csv(DATA_CSV)
    # use 'notes' field as text if it's informative, otherwise synthesize
    if 'notes' in df_all.columns and df_all['notes'].notna().any():
        sample = df_all[['notes']].dropna().drop_duplicates().rename(columns={'notes':'text'}).head(1000)
        # improved naive label assignment using keywords (negative -> price up / risk)
        def label_from_text(t):
            t = str(t).lower()
            if any(x in t for x in ['increase','rising','higher','spike','up','surge']):
                return 'negative'
            if any(x in t for x in ['drop','decrease','down','lower','fall','decline']):
                return 'positive'
            return 'neutral'
        sample['label'] = sample['text'].apply(label_from_text)
        return sample

    # last fallback: small synthetic dataset
    data = [
        ("Market demand increasing, prices expected to rise", 'negative'),
        ("Supply stable and prices steady", 'neutral'),
        ("Lower transport costs may reduce price", 'positive'),
        ("Fuel prices hit, logistics cost up", 'negative'),
        ("New imports ease supply, prices down", 'positive'),
    ]
    return pd.DataFrame(data, columns=['text','label'])

def train_and_save():
    df = load_corpus()
    # If the corpus is too small for train/test split, fall back to a small synthetic dataset
    if len(df) < 5:
        print('Corpus too small (found', len(df), 'rows). Using synthetic fallback dataset.')
        data = [
            ("Market demand increasing, prices expected to rise", 'negative'),
            ("Supply stable and prices steady", 'neutral'),
            ("Lower transport costs may reduce price", 'positive'),
            ("Fuel prices hit, logistics cost up", 'negative'),
            ("New imports ease supply, prices down", 'positive'),
            ("Local demand slumps; construction slow", 'negative'),
            ("Government incentives boost local projects", 'positive'),
            ("Transport disruptions causing price spikes", 'negative')
        ]
        df = pd.DataFrame(data, columns=['text','label'])
    texts = df['text'].astype(str).tolist()
    labels = df['label'].astype(str).tolist()
    from sklearn.model_selection import train_test_split
    from collections import Counter
    label_counts = Counter(labels)
    stratify_param = labels
    if len(label_counts) == 0 or min(label_counts.values()) < 2:
        stratify_param = None
    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=stratify_param
    )
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), max_features=8000, stop_words='english')),
        ('clf', LogisticRegression(max_iter=2000))
    ])
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    print('NLP training complete. Report:\n')
    print(classification_report(y_test, preds))
    out_path = os.path.join(MODELS_DIR, 'nlp_model.joblib')
    dump(pipeline, out_path)
    print('Saved NLP model to', out_path)

if __name__ == '__main__':
    train_and_save()
