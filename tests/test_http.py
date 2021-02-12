import pytest
from plastron.http import Repository
from plastron.exceptions import RESTAPIException


@pytest.fixture()
def repo_base_config():
    """Required parameters for Repository configuration"""
    return {
        'REST_ENDPOINT': 'http://base-host.com/rest',
        'RELPATH': '/pcdm',
        'LOG_DIR': '/logs',
    }


@pytest.fixture()
def repo_forwarded_config(repo_base_config):
    """base_config with FORWARDED_HOST and FORWARDED_PROTO"""
    repo_base_config['FORWARDED_HOST'] = 'forwarded-host.com'
    repo_base_config['FORWARDED_PROTO'] = 'https'
    return repo_base_config


class MockRepository(Repository):
    def __init__(self, config, ua_string=None, on_behalf_of=None):
        super().__init__(config, ua_string, on_behalf_of)

    def set_mock_response(self, mock_response):
        self.mock_response = mock_response

    def head(self, uri, **kwargs):
        return self.mock_response

    def post(self, url, **kwargs):
        return self.mock_response


class MockResponse:
    def __init__(self, status_code, headers=None, links=None):
        self.status_code = status_code
        self.headers = headers
        self.links = links


def test_get_description_uri_failed_response(repo_base_config):
    repo = MockRepository(repo_base_config)
    repo.set_mock_response(MockResponse(404))
    with pytest.raises(RESTAPIException):
        repo.get_description_uri('http://example.com/foo')


def test_get_description_uri_no_describedby(repo_base_config):
    repo = MockRepository(repo_base_config)
    repo.set_mock_response(MockResponse(200, links={}))
    description_uri = repo.get_description_uri('uri')
    assert 'uri' == description_uri


def test_get_description_uri_no_describedby(repo_base_config):
    repo = MockRepository(repo_base_config)
    links = {'describedby': {'url': 'describedby_url'}}
    repo.set_mock_response(MockResponse(200, links=links))

    description_uri = repo.get_description_uri('uri')
    assert 'describedby_url' == description_uri


def test_create_with_no_describedby(repo_base_config):
    repo = MockRepository(repo_base_config)
    headers = {'Location': 'location_url'}
    links = {}
    repo.set_mock_response(MockResponse(201, headers=headers, links=links))

    resource_uri = repo.create()
    assert 'location_url' == resource_uri.uri
    assert 'location_url' == resource_uri.description_uri


def test_create_with_describedby(repo_base_config):
    repo = MockRepository(repo_base_config)
    headers = {'Location': 'location_url'}
    links = {'describedby': {'url': 'describedby_url'}}
    repo.set_mock_response(MockResponse(201, headers=headers, links=links))

    resource_uri = repo.create()
    assert 'location_url' == resource_uri.uri
    assert 'describedby_url' == resource_uri.description_uri


def test_process_description_uri_no_describedby_no_forwards(repo_base_config):
    repo = MockRepository(repo_base_config)
    response = MockResponse(201, links={})

    description_uri = repo.process_description_uri('uri', response)
    assert 'uri' == description_uri


def test_process_description_uri_with_describedby_no_forwards(repo_base_config):
    repo = MockRepository(repo_base_config)
    response = MockResponse(201, links={'describedby': {'url': 'describedby_url'}})

    description_uri = repo.process_description_uri('uri', response)
    assert 'describedby_url' == description_uri


def test_process_description_uri_no_describedby_with_forwards(repo_forwarded_config):
    repo = MockRepository(repo_forwarded_config)
    response = MockResponse(201, links={})

    description_uri = repo.process_description_uri('http://base-host.com/rest', response)
    assert 'https://forwarded-host.com/rest' == description_uri


def test_process_description_uri_with_describedby_with_forwards(repo_forwarded_config):
    repo = MockRepository(repo_forwarded_config)
    response = MockResponse(201, links={'describedby': {'url': 'http://base-host.com/rest/abc'}})

    description_uri = repo.process_description_uri('http://base-host.com/rest', response)
    assert 'https://forwarded-host.com/rest/abc' == description_uri


def test_create_with_describedby_and_forwarded_params(repo_forwarded_config):
    repo = MockRepository(repo_forwarded_config)
    headers = {'Location': 'location_url'}
    links = {'describedby': {'url': 'http://localhost:8080/'}}
    repo.set_mock_response(MockResponse(201, headers=headers, links=links))

    resource_uri = repo.create()

    assert resource_uri.uri.startswith('https://forwarded-host.com/')
    assert resource_uri.description_uri.startswith('https://forwarded-host.com/')


def test_forwarded_params_sets_headers(repo_forwarded_config):
    config = repo_forwarded_config

    repository = Repository(config)

    assert 'X-Forwarded-Host' in repository.session.headers.keys()
    assert 'X-Forwarded-Proto' in repository.session.headers.keys()
    assert 'forwarded-host.com' == repository.session.headers['X-Forwarded-Host']
    assert 'https' == repository.session.headers['X-Forwarded-Proto']


def test_forwarded_params_are_optional(repo_base_config):
    config = repo_base_config

    repository = Repository(config)

    assert not ('X-Forwarded-Host' in repository.session.headers.keys())
    assert not ('X-Forwarded-Proto' in repository.session.headers.keys())
