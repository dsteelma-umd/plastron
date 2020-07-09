import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

logger = logging.getLogger(__name__)


class InboxEventHandler(FileSystemEventHandler):
    """Triggers message processing when a file is added in the
       inbox directory."""
    # Note to maintainers: The original implementation of this class included
    # both "on_created" and "on_modified" event handlers. On Mac OS X, new file
    # creation only triggers the "on_created" event. On Linux, new file
    # creation triggers both an "on_created" event and "on_modified" event,
    # leading to duplicate processing (see LIBFCREPO-821).
    def __init__(self, command_listener, message_box):
        self.command_listener = command_listener
        self.message_box = message_box

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent):
            logger.info(f"Triggering inbox processing due to {event}")
            message = self.message_box.message_class.read(event.src_path)
            response_handler = self.command_listener.asynchronous_response_handler(message.id)
            self.command_listener.process_message(message, response_handler)


class InboxWatcher:
    """
    Watches for changes to the inbox directory, in order to trigger message
    processing via InboxEventHandler
    """
    def __init__(self, command_listener, message_box):
        """Constructs the watchdog Observer"""
        self.observer = Observer()
        self.observer.schedule(InboxEventHandler(command_listener, message_box), message_box.dir, recursive=True)

    def start(self):
        """Start the watcher"""
        logger.debug(f"Starting InboxWatcher")
        self.observer.start()

    def stop(self):
        """Stop the watcher"""
        logger.debug(f"Stopping InboxWatcher")
        self.observer.unschedule_all()
        self.observer.stop()
