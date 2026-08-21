import argparse
import json
import os
import queue
import signal
import sys
import threading
from importlib.metadata import PackageNotFoundError
from types import FrameType
from typing import Any, Optional

import jsonschema
from wb_common.mqtt_client import MQTTClient

from wb.python_service_template.version import get_version

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_CONFIG_ERROR = 6

# путь к пользовательским настройкам по умолчанию
CONFIG_FILEPATH = "/etc/wb-python-service-template.conf"
# указываем путь к статической схеме
SCHEMA_FILEPATH = "/usr/share/wb-mqtt-confed/schemas/wb-python-service-template.schema.json"


class _PrintVersionAction(argparse.Action):
    """
    Reads the version only when the flag is actually used.
    """

    def __init__(self, option_strings: list[str], dest: str, **kwargs: Any) -> None:
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        option_string: Optional[str] = None,
    ) -> None:
        try:
            print(get_version())
        except PackageNotFoundError:
            parser.exit(EXIT_FAILURE, "Package metadata not found, install the package to use --version\n")
        parser.exit()


class OneThreadServiceTemplate:  # pylint:disable=too-few-public-methods
    """
    Example service that serves MQTT messages in the current thread.

    Suits a service whose only job is to react to an incoming message.
    """

    def __init__(self) -> None:
        signal.signal(signal.SIGINT, self._signal_handler)

        self._client = MQTTClient("test_client", is_threaded=False)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._mqtt_was_disconected = False
        self._count = 0
        self._error = None

    def _on_connect(self, _client: MQTTClient, _userdata: Any, _flags: Any, rc: int) -> None:
        if rc != 0:
            print("MQTT client connected with rc %s", rc)
            return

        print("MQTT client connected")
        print("Subscribe to topics")
        self._client.subscribe("/devices/power_status/controls/Vin")
        print("Publish RPC endpoints")
        # публикация rpc

        if self._mqtt_was_disconected:
            print("Republish controls")
            # перепубликация контролов

    def _on_disconnect(self, _client: MQTTClient, _userdata: Any, _flags: Any) -> None:
        self._mqtt_was_disconected = True
        print("MQTT client disconnected")

    def _on_message(self, _client: MQTTClient, _userdata: Any, _msg: Any) -> None:
        self._count += 1
        if self._count == 10:
            self._error = RuntimeError("Simulate failure")
            self._client.stop()

        print("Do work, publish result")
        # выполнение работы после получения сообщения и публикация результата

    def _signal_handler(self, _signum: int, _frame: Optional[FrameType]) -> None:
        print("Termination signal received, stopping MQTT client")
        self._client.stop()

    def run(self) -> int:
        """
        Serves messages until the client is stopped by a signal or by a failure.

        Returns:
            EXIT_SUCCESS on a clean stop, EXIT_FAILURE if the connection failed or the work did.
        """
        try:
            print("Starting MQTT client")
            self._client.start()
            self._client.loop_forever()
        except ConnectionError:
            print("MQTT connection error!")
            return EXIT_FAILURE

        if self._error:
            print(f"Error occurred: {self._error}")
            return EXIT_FAILURE

        return EXIT_SUCCESS


class ThreadedServiceTemplate:  # pylint:disable=too-few-public-methods
    """
    Example service that serves MQTT messages in a separate thread.

    Suits a service with its own work loop, which has to keep going regardless of messages.
    """

    def __init__(self) -> None:
        self._term_event = threading.Event()
        self._queue = queue.Queue()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGHUP, self._signal_handler)

        self._client = MQTTClient("test_client")
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._mqtt_was_disconected = False

    def _on_connect(self, _client: MQTTClient, _userdata: Any, _flags: Any, rc: int) -> None:
        if rc != 0:
            print("MQTT client connected with rc %s", rc)
            return

        print("MQTT client connected")
        print("Subscribe to topics")
        self._client.subscribe("/devices/power_status/controls/Vin")
        print("Publish RPC endpoints")
        # публикация rpc

        if self._mqtt_was_disconected:
            print("Republish controls")
            # перепубликация контролов

    def _on_disconnect(self, _client: MQTTClient, _userdata: Any, _flags: Any) -> None:
        self._mqtt_was_disconected = True
        print("MQTT client disconnected")

    def _on_message(self, _client: MQTTClient, _userdata: Any, msg: Any) -> None:
        self._queue.put(msg.payload.decode("utf-8"))

    def _signal_handler(self, _signum: int, _frame: Optional[FrameType]) -> None:
        print("Termination signal received, stopping MQTT client")
        self._term_event.set()
        self._client.stop()

    def _do_work(self) -> None:
        count = 0
        while count != 10 and not self._term_event.is_set():
            if not self._queue.empty():
                count += 1
                message = self._queue.get()
                print("Handling new message " + message)
        if count == 10:
            raise RuntimeError("Simulate failure")

    def run(self) -> int:
        """
        Runs the work loop until it finishes or a signal arrives.

        Returns:
            EXIT_SUCCESS on a clean stop, EXIT_FAILURE if the connection failed or the work did.
        """
        try:
            print("Starting MQTT client")
            self._client.start()
            self._do_work()
        except ConnectionError:
            print("MQTT connection error!")
            return EXIT_FAILURE
        except RuntimeError:
            print("Failure! Stopping MQTT client")
            self._client.stop()
            return EXIT_FAILURE

        return EXIT_SUCCESS


def main(argv: list[str]) -> int:
    """
    Reads the configuration and runs the service the configuration asks for.

    Args:
        argv: Command line arguments, argv[0] is the program name and is not used.

    Returns:
        One of EXIT_SUCCESS, EXIT_FAILURE or EXIT_CONFIG_ERROR.
    """
    parser = argparse.ArgumentParser(
        description="MQTT Python Service Template", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--version", action=_PrintVersionAction, help="show package version and exit")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=CONFIG_FILEPATH,
        help="Path to configuration file",
    )
    args = parser.parse_args(argv[1:])
    if not os.path.isfile(args.config):
        print(f"Configuration file not found: {args.config}")
        return EXIT_CONFIG_ERROR

    with open(args.config, "r", encoding="utf-8") as config_file, open(
        SCHEMA_FILEPATH, "r", encoding="utf-8"
    ) as schema_file:
        config = json.load(config_file)
        schema = json.load(schema_file)
        try:
            jsonschema.validate(
                instance=config, schema=schema, format_checker=jsonschema.draft4_format_checker
            )
        except jsonschema.ValidationError as e:
            print(f"Configuration validation failed: {e.message}")
            return EXIT_CONFIG_ERROR

    if config["mode"] == "one_thread":
        service = OneThreadServiceTemplate()
    else:
        service = ThreadedServiceTemplate()
    return service.run()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
