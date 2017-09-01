"""Unit tests for counterfactually fair models."""

import numpy as np
import pytest

from themis_ml.linear_model import counterfactually_fair_models
from themis_ml.checks import is_binary, is_continuous

SEED = 10


@pytest.fixture
def data():
    return {
        "bin": create_binary_X(),
        "cont": create_continuous_X()}


def create_X(X_data_):
    return np.concatenate([
        X_data_["bin"], X_data_["cont"],
        X_data_["bin"], X_data_["cont"]], axis=1)


def create_binary_X():
    np.random.seed(SEED)
    return np.random.randint(0, 2, (10, 3))


def create_continuous_X():
    np.random.seed(SEED)
    return np.random.randint(0, 100, (10, 3))


def create_y():
    return np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])


def create_s():
    return np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])


def test_get_binary_X_index(data):
    X = create_X(data)
    expected = np.concatenate([data["bin"], data["bin"]], axis=1)
    binary_index = counterfactually_fair_models._get_binary_X_index(X)
    assert (X[:, binary_index] == expected).all()


def test_get_continuous_X(data):
    X = create_X(data)
    expected = np.concatenate([data["cont"], data["cont"]], axis=1)
    continuous_index = counterfactually_fair_models._get_continuous_X_index(X)
    assert (X[:, continuous_index] == expected).all()


def test_fit_predict(data):
    """Test happy path of LinearACFClassifier `fit` and `predict` methods."""
    X = create_X(data)
    y = create_y()
    s = create_s()
    for residual_type in ["pearson", "deviance", "absolute"]:
        lin_acf = counterfactually_fair_models.LinearACFClassifier(
            binary_residual_type=residual_type)
        lin_acf.fit(X, y, s)
        lin_acf_pred_proba = lin_acf.predict_proba(X, s)[:, 1]
        assert(lin_acf.fit_residuals_ ==
               lin_acf._compute_residuals_on_predict(X, s)).all()
        assert is_binary(lin_acf.predict(X, s))
        assert is_continuous(lin_acf_pred_proba)
        assert max(lin_acf_pred_proba) < 1
        assert min(lin_acf_pred_proba) > 0


def test_predict_value_error(data):
    """Raise ValueError if X doesn't have expected number of variables."""
    X = create_X(data)
    s = create_s()
    lin_acf = counterfactually_fair_models.LinearACFClassifier()
    lin_acf.fit(X, create_y(), s)
    with pytest.raises(ValueError):
        # pass in just a subset of the input variables
        lin_acf.predict(X[:, 5], s)
        lin_acf.predict_proba(X[:, 5], s)


def test_invalid_binary_residual_type(data):
    with pytest.raises(ValueError):
        counterfactually_fair_models.LinearACFClassifier(
            binary_residual_type="foobar")
