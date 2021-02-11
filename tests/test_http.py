import pytest
from plastron.http import Repository


@pytest.fixture()
def base_config():
    return {
        'REST_ENDPOINT': 'http://foobar.com/rest',
        'RELPATH': '/pcdm',
        'LOG_DIR': '/logs',
    }


def test_forwarded_params_sets_headers(base_config):
    config = base_config
    config['FORWARDED_HOST'] = 'example.com'
    config['FORWARDED_PROTO'] = 'https'

    repository = Repository(config)

    assert 'X-Forwarded-Host' in repository.session.headers.keys()
    assert 'X-Forwarded-Proto' in repository.session.headers.keys()
    assert 'example.com' == repository.session.headers['X-Forwarded-Host']
    assert 'https' == repository.session.headers['X-Forwarded-Proto']


def test_forwarded_params_are_optional(base_config):
    config = base_config
    repository = Repository(config)

    assert not ('X-Forwarded-Host' in repository.session.headers.keys())
    assert not ('X-Forwarded-Proto' in repository.session.headers.keys())
