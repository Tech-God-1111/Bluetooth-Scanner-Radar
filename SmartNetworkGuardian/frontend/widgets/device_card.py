from frontend.widgets.status_card import StatusCard

class DeviceCard(StatusCard):
    def __init__(self, parent=None):
        super().__init__("Discovered devices", "0", parent)
