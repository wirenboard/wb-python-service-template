from wb.python_service_template import main


def test_missing_config_returns_config_error():
    exit_code = main.main(["wb-foo", "-c", "/nonexistent/does-not-exist.conf"])
    assert exit_code == main.EXIT_CONFIG_ERROR
