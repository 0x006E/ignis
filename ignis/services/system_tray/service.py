from __future__ import annotations
from ignis.utils import Utils
from ignis.dbus import DBusService
from gi.repository import Gio, GLib, GObject  # type: ignore
from loguru import logger
from ignis.base_service import BaseService
from .item import SystemTrayItem


class SystemTrayService(BaseService):
    """
    A system tray, where application icons are placed.

    Signals:
        - **"added"** (:class:`~ignis.services.system_tray.SystemTrayItem`): Emitted when a new item is added.

    Properties:
        - **items** (list[:class:`~ignis.services.system_tray.SystemTrayItem`], read-only): A list of items.

    **Example usage:**

    .. code-block:: python

        from ignis.services.system_tray import SystemTrayService

        system_tray = SystemTrayService.get_default()

        system_tray.connect("added", lambda x, item: print(item.title))
    """

    __gsignals__ = {
        "added": (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (GObject.Object,)),
    }

    def __init__(self):
        super().__init__()
        self._items: dict[str, SystemTrayItem] = {}

        self.__dbus: DBusService = DBusService(
            name="org.kde.StatusNotifierWatcher",
            object_path="/StatusNotifierWatcher",
            info=Utils.load_interface_xml("org.kde.StatusNotifierWatcher"),
            on_name_lost=lambda x, y: logger.error(
                "Another system tray is already running. Try to close other status bars/graphical shells."
            ),
        )

        self.__dbus.register_dbus_property(
            name="ProtocolVersion", method=self.__ProtocolVersion
        )
        self.__dbus.register_dbus_property(
            name="IsStatusNotifierHostRegistered",
            method=self.__IsStatusNotifierHostRegistered,
        )
        self.__dbus.register_dbus_property(
            name="RegisteredStatusNotifierItems",
            method=self.__RegisteredStatusNotifierItems,
        )

        self.__dbus.register_dbus_method(
            name="RegisterStatusNotifierItem", method=self.__RegisterStatusNotifierItem
        )

    @GObject.Property
    def items(self) -> list[SystemTrayItem]:
        return list(self._items.values())

    def __ProtocolVersion(self) -> GLib.Variant:
        return GLib.Variant("i", 0)

    def __IsStatusNotifierHostRegistered(self) -> GLib.Variant:
        return GLib.Variant("b", True)

    def __RegisteredStatusNotifierItems(self) -> GLib.Variant:
        return GLib.Variant("as", list(self._items.keys()))

    def __RegisterStatusNotifierItem(
        self, invocation: Gio.DBusMethodInvocation, service: str
    ) -> None:
        if service.startswith("/"):
            object_path = service
            bus_name = invocation.get_sender()

        else:
            object_path = "/StatusNotifierItem"
            bus_name = service

        invocation.return_value(None)

        item = SystemTrayItem(bus_name, object_path)
        item.connect("ready", self.__on_item_ready, bus_name, object_path)

    def __on_item_ready(
        self, item: SystemTrayItem, bus_name: str, object_path: str
    ) -> None:
        self._items[bus_name] = item
        item.connect("removed", self.__remove_item, bus_name)
        self.emit("added", item)
        self.notify("items")
        self.__dbus.emit_signal(
            "StatusNotifierItemRegistered",
            GLib.Variant("(s)", (bus_name + object_path,)),
        )

    def __remove_item(self, x, bus_name: str) -> None:
        self._items.pop(bus_name)
        self.notify("items")
        self.__dbus.emit_signal(
            "StatusNotifierItemUnregistered", GLib.Variant("(s)", (bus_name,))
        )