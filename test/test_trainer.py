import pytest
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.base import TransformerMixin, ClassifierMixin
from trainer.task import get_preprocessor, get_model, get_pipe
import pandas as pd

def test_get_preprocessor():
    preprocessor = get_preprocessor()
    assert preprocessor is not None
    assert isinstance(preprocessor, TransformerMixin)
    assert hasattr(preprocessor, 'fit')
    assert hasattr(preprocessor, 'transform')

def test_get_model():
    model = get_model()
    assert model is not None
    assert isinstance(model, ClassifierMixin)
    assert hasattr(model, 'fit')
    assert hasattr(model, 'predict')

def test_get_pipe():
    pipe = get_pipe()
    assert pipe is not None
    assert isinstance(pipe, Pipeline)
    assert 'preprocessor' in pipe.named_steps
    assert 'model' in pipe.named_steps

def test_model_training():
    iris = load_iris(as_frame=True)
    iris_df = pd.concat([iris.data, iris.target], axis=1)

    # Use a portion of the dataset to reduce training time
    PORTION = 0.1
    df = iris_df.groupby("target").apply(lambda x: x.sample(frac=PORTION)).reset_index(drop=True)
    
    y = df.pop("target")
    X = df

    pipe = get_pipe()
    pipe.fit(X, y)
    y_pred = pipe.predict(X)

    assert y_pred is not None
    assert len(y_pred) == len(y)
    assert len(set(y_pred)) == len(set(y))
