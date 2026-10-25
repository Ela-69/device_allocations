"""
Mã sinh viên : 202418930
Họ tên: Dương Tùng Lâm
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Generic, Optional, Protocol, Sequence, TypeVar


class DeviceStatus(Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    UNDER_MAINTENANCE = "UnderMaintenance"

    @property
    def label(self) -> str:
        """Nhãn tiếng Việt dùng khi hiển thị (giá trị enum giữ nguyên)."""
        return _STATUS_LABELS[self]


_STATUS_LABELS = {
    DeviceStatus.AVAILABLE: "Sẵn sàng",
    DeviceStatus.BORROWED: "Đang được mượn",
    DeviceStatus.UNDER_MAINTENANCE: "Đang bảo trì",
}


class DuplicateIdException(Exception):
    def __init__(self, duplicate_id: str):
        super().__init__(f"Trùng mã: {duplicate_id}")
        self.duplicate_id = duplicate_id


class NoSuitableItemException(Exception):
    def __init__(self, message: str = "Không có thiết bị phù hợp"):
        super().__init__(message)


class DeviceNotReadyException(Exception):
    def __init__(self, device_id: str, current_status: DeviceStatus):
        super().__init__(f"Thiết bị {device_id} không thể thực hiện thao tác, trạng thái: {current_status.label}")
        self.device_id = device_id
        self.current_status = current_status


class IIdentifiable(Protocol):
    @property
    def id(self) -> str: ...


def _require_text(value, field: str) -> str:
    if value is None or value == "":
        raise ValueError(f"{field} không hợp lệ")
    return value


def _require_percent(value, field: str) -> int:
    if not isinstance(value, int) or not 0 <= value <= 100:
        raise ValueError(f"{field} phải là số nguyên từ 0 đến 100")
    return value


class TeachingDevice(ABC):
    # Tên loại thiết bị hiển thị bằng tiếng Việt; lớp dẫn xuất ghi đè.
    kind_label = "Thiết bị"

    def __init__(self, id: str, name: str, storage_location: str):
        self._id = _require_text(id, "Mã")
        self._name = _require_text(name, "Tên")
        self._storage_location = _require_text(storage_location, "Vị trí lưu trữ")
        self._status = DeviceStatus.AVAILABLE

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def storage_location(self) -> str:
        return self._storage_location

    @property
    def status(self) -> DeviceStatus:
        return self._status

    @abstractmethod
    def is_ready_for_use(self) -> bool: ...

    @abstractmethod
    def get_default_priority_score(self) -> float: ...

    def borrow(self) -> None:
        if not self.is_ready_for_use():
            raise DeviceNotReadyException(self._id, self._status)
        self._status = DeviceStatus.BORROWED

    def return_device(self) -> None:
        if self._status == DeviceStatus.AVAILABLE:
            raise DeviceNotReadyException(self._id, self._status)
        self._status = DeviceStatus.AVAILABLE

    def send_to_maintenance(self) -> None:
        if self._status == DeviceStatus.BORROWED:
            raise DeviceNotReadyException(self._id, self._status)
        self._status = DeviceStatus.UNDER_MAINTENANCE

    def describe(self) -> str:
        return f"[{self.kind_label}] {self._id} | {self._name} | {self._storage_location} | {self._status.label}"


class ProjectorRemote(TeachingDevice):
    kind_label = "Điều khiển máy chiếu"

    def __init__(self, id: str, name: str, storage_location: str, battery_level: int):
        super().__init__(id, name, storage_location)
        self._battery_level = _require_percent(battery_level, "Mức pin")

    @property
    def battery_level(self) -> int:
        return self._battery_level

    def is_ready_for_use(self) -> bool:
        return self._status == DeviceStatus.AVAILABLE and self._battery_level > 20

    def get_default_priority_score(self) -> float:
        return float(self._battery_level)

    def describe(self) -> str:
        return f"{super().describe()} | pin={self._battery_level}"


class AirConditionerRemote(TeachingDevice):
    kind_label = "Điều khiển điều hòa"

    def __init__(self, id: str, name: str, storage_location: str, compatible_rooms):
        super().__init__(id, name, storage_location)
        self._compatible_rooms = frozenset(compatible_rooms)

    @property
    def compatible_rooms(self) -> frozenset:
        return self._compatible_rooms

    def is_compatible_with(self, room_id: str) -> bool:
        return room_id in self._compatible_rooms

    def is_ready_for_use(self) -> bool:
        return self._status == DeviceStatus.AVAILABLE

    def get_default_priority_score(self) -> float:
        return 100.0 if self._compatible_rooms else 0.0

    def describe(self) -> str:
        return f"{super().describe()} | phòng={sorted(self._compatible_rooms)}"


class WirelessMicrophone(TeachingDevice):
    kind_label = "Micro không dây"

    def __init__(self, id: str, name: str, storage_location: str, battery_level: int, signal_quality: int):
        super().__init__(id, name, storage_location)
        self._battery_level = _require_percent(battery_level, "Mức pin")
        self._signal_quality = _require_percent(signal_quality, "Chất lượng tín hiệu")

    @property
    def battery_level(self) -> int:
        return self._battery_level

    @property
    def signal_quality(self) -> int:
        return self._signal_quality

    def is_ready_for_use(self) -> bool:
        return (
            self._status == DeviceStatus.AVAILABLE
            and (self._battery_level >= 30 or self._signal_quality >= 40)
        )

    def get_default_priority_score(self) -> float:
        return (self._battery_level + self._signal_quality) // 2

    def describe(self) -> str:
        return f"{super().describe()} | pin={self._battery_level} | tín hiệu={self._signal_quality}"


T = TypeVar("T", bound=IIdentifiable)
D = TypeVar("D", bound=TeachingDevice)
S = TypeVar("S")


class IRepository(ABC, Generic[T]):
    @abstractmethod
    def add(self, item: T) -> None: ...

    @abstractmethod
    def remove(self, id: str) -> bool: ...

    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]: ...

    @abstractmethod
    def get_all(self) -> Sequence[T]: ...

    @abstractmethod
    def find_all(self, condition: Callable[[T], bool]) -> Sequence[T]: ...


class InMemoryRepository(IRepository[T]):
    def __init__(self):
        self._items: list = []

    def add(self, item: T) -> None:
        if item is None:
            raise ValueError("Không chấp nhận phần tử null")
        if self.find_by_id(item.id) is not None:
            raise DuplicateIdException(item.id)
        self._items.append(item)

    def remove(self, id: str) -> bool:
        self._items = [x for x in self._items if x.id != id]
        return True

    def find_by_id(self, id: str) -> Optional[T]:
        for item in self._items:
            if item.id == id:
                return item
        return None

    def get_all(self) -> Sequence[T]:
        return self._items

    def find_all(self, condition: Callable[[T], bool]) -> Sequence[T]:
        return [x for x in self._items if condition(x)]


class ISelectionStrategy(ABC, Generic[S]):
    @abstractmethod
    def select(self, candidates: Sequence[S]) -> S: ...


class HighestPriorityStrategy(ISelectionStrategy[S]):
    def __init__(self, score_selector: Callable[[S], float]):
        self._score_selector = score_selector

    def select(self, candidates: Sequence[S]) -> S:
        if not candidates:
            raise NoSuitableItemException()
        candidates.sort(key=self._score_selector, reverse=True)
        return candidates[0]


class FirstAvailableStrategy(ISelectionStrategy[S]):
    def select(self, candidates: Sequence[S]) -> S:
        # Danh sách rỗng phải báo lỗi tiếng Việt thay vì IndexError mặc định của Python.
        if not candidates:
            raise NoSuitableItemException()
        return candidates[0]


class AllocationService(Generic[D]):
    def __init__(self, repository: IRepository[D], strategy: ISelectionStrategy[D]):
        if repository is None or strategy is None:
            raise ValueError("repository và strategy là bắt buộc")
        self._repository = repository
        self._strategy = strategy

    def change_strategy(self, new_strategy: ISelectionStrategy[D]) -> None:
        self._strategy = new_strategy

    def allocate(self, additional_condition: Optional[Callable[[D], bool]] = None) -> D:
        ready = self._repository.find_all(lambda d: d.is_ready_for_use())
        if additional_condition is not None:
            ready = [d for d in ready if additional_condition(d)]
        chosen = self._strategy.select(ready)
        chosen.borrow()
        return chosen


def read_text(prompt: str) -> str:
    return input(prompt).strip()


def read_int(prompt: str, low: int, high: int) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            value = int(raw)
        except ValueError:
            print("Vui lòng nhập số nguyên.")
            continue
        if low <= value <= high:
            return value
        print(f"Giá trị phải trong khoảng {low}..{high}.")


KINDS = {
    1: "Điều khiển máy chiếu",
    2: "Điều khiển điều hòa",
    3: "Micro không dây",
}

DEFAULT_STRATEGY_NAME = "Chọn thiết bị sẵn sàng đầu tiên"

STRATEGIES = {
    1: (DEFAULT_STRATEGY_NAME, lambda: FirstAvailableStrategy()),
    2: ("Chọn thiết bị có điểm ưu tiên cao nhất", lambda: HighestPriorityStrategy(lambda d: d.get_default_priority_score())),
}


class App:
    def __init__(self):
        self.repos = {k: InMemoryRepository() for k in KINDS}
        self.services = {
            k: AllocationService(self.repos[k], FirstAvailableStrategy()) for k in KINDS
        }
        self.strategy_names = {k: DEFAULT_STRATEGY_NAME for k in KINDS}

    def pick_kind(self) -> int:
        for k, v in KINDS.items():
            print(f"  {k}. {v}")
        return read_int("Chọn loại: ", 1, 3)

    def add_device(self, kind: int) -> None:
        id_ = read_text("Mã: ")
        name = read_text("Tên: ")
        location = read_text("Vị trí lưu trữ: ")
        if kind == 1:
            device = ProjectorRemote(id_, name, location, read_int("Mức pin (0-100): ", 0, 100))
        elif kind == 2:
            rooms = [r.strip() for r in read_text("Phòng tương thích (cách nhau bằng dấu phẩy): ").split(",") if r.strip()]
            device = AirConditionerRemote(id_, name, location, rooms)
        else:
            battery = read_int("Mức pin (0-100): ", 0, 100)
            signal = read_int("Chất lượng tín hiệu (0-100): ", 0, 100)
            device = WirelessMicrophone(id_, name, location, battery, signal)
        self.repos[kind].add(device)
        print("Đã thêm:", device.describe())

    def find_device(self) -> None:
        id_ = read_text("Mã cần tìm: ")
        for kind, repo in self.repos.items():
            device = repo.find_by_id(id_)
            if device is not None:
                print(device.describe())
                return
        print("Không tìm thấy.")

    def list_devices(self, only_ready: bool) -> None:
        print("  0. Tất cả thiết bị")
        for k, name in KINDS.items():
            print(f"  {k}. {name}")
        kind = read_int("Chọn loại (0 để xem tất cả): ", 0, 3)
        if kind == 0:
            items = [
                device
                for repo in self.repos.values()
                for device in repo.get_all()
            ]
        else:
            items = self.repos[kind].get_all()
        if only_ready:
            items = [d for d in items if d.is_ready_for_use()]
        if not items:
            print("Danh sách rỗng.")
        for d in items:
            print(d.describe())

    def allocate(self) -> None:
        kind = self.pick_kind()
        condition = None
        if kind == 2:
            room = read_text("Mã phòng (để trống nếu không lọc): ")
            if room:
                condition = lambda d: d.is_compatible_with(room)
        try:
            device = self.services[kind].allocate(condition)
        except (NoSuitableItemException, DeviceNotReadyException) as ex:
            print("Lỗi:", ex)
            return
        print("Đã cấp phát:", device.describe())

    def change_strategy(self) -> None:
        kind = self.pick_kind()
        for k, (name, _) in STRATEGIES.items():
            print(f"  {k}. {name}")
        choice = read_int("Chọn chiến lược: ", 1, len(STRATEGIES))
        name, factory = STRATEGIES[choice]
        self.services[kind].change_strategy(factory())
        self.strategy_names[kind] = name
        print("Chiến lược hiện tại:", name)

    def return_device(self) -> None:
        kind = self.pick_kind()
        device = self.repos[kind].find_by_id(read_text("Mã thiết bị: "))
        if device is None:
            print("Không tìm thấy.")
            return
        device.return_device()
        print("Đã trả:", device.describe())

    def maintenance(self) -> None:
        kind = self.pick_kind()
        device = self.repos[kind].find_by_id(read_text("Mã thiết bị: "))
        if device is None:
            print("Không tìm thấy.")
            return
        device.send_to_maintenance()
        print(device.describe())

    def remove_device(self) -> None:
        kind = self.pick_kind()
        removed = self.repos[kind].remove(read_text("Mã thiết bị: "))
        print("Đã xóa." if removed else "Không tìm thấy mã.")

    def show_strategies(self) -> None:
        for k, name in self.strategy_names.items():
            print(f"{KINDS[k]}: {name}")

    def show_total_devices(self) -> None:
        total = sum(len(repo.get_all()) for repo in self.repos.values())
        print(f"Tổng số lượng thiết bị: {total}")

    def load_sample_data(self) -> None:
        # Kho 1: máy chiếu
        self.repos[1].add(ProjectorRemote("PRJ-001", "Remote Epson A", "Kho 1", 85))
        self.repos[1].add(ProjectorRemote("PRJ-002", "Remote Epson B", "Kho 1", 55))
        self.repos[1].add(ProjectorRemote("PRJ-003", "Remote Sony C", "Kho 2", 15))
        # Kho 2: điều hòa 
        self.repos[2].add(AirConditionerRemote("AC-001", "Remote Daikin", "Kho 1", ["A101", "A102", "A203"]))
        self.repos[2].add(AirConditionerRemote("AC-002", "Remote Panasonic", "Kho 2", ["B201", "B202"]))
        # Kho 3: micro 
        self.repos[3].add(WirelessMicrophone("MIC-001", "Micro Shure A", "Kho 1", 90, 70))
        self.repos[3].add(WirelessMicrophone("MIC-002", "Micro Shure B", "Kho 1", 40, 95))
        self.repos[3].add(WirelessMicrophone("MIC-003", "Micro Sennheiser C", "Kho 2", 25, 90))

    def run(self) -> None:
        menu = [
            ("Thêm điều khiển máy chiếu", lambda: self.add_device(1)),
            ("Thêm điều khiển điều hòa", lambda: self.add_device(2)),
            ("Thêm micro không dây", lambda: self.add_device(3)),
            ("Tìm thiết bị theo mã", self.find_device),
            ("Liệt kê tất cả thiết bị", lambda: self.list_devices(False)),
            ("Lọc thiết bị sẵn sàng", lambda: self.list_devices(True)),
            ("Cấp phát thiết bị", self.allocate),
            ("Đổi chiến lược lựa chọn", self.change_strategy),
            ("Xem chiến lược hiện tại", self.show_strategies),
            ("Xem tổng số lượng thiết bị", self.show_total_devices),
            ("Trả thiết bị", self.return_device),
            ("Chuyển thiết bị sang bảo trì", self.maintenance),
            ("Xóa thiết bị", self.remove_device),
        ]
        while True:
            print("\n===== MENU =====")
            for i, (label, _) in enumerate(menu, 1):
                print(f"{i:>2}. {label}")
            print(" 0. Thoát")
            choice = read_int("Chọn: ", 0, len(menu))
            if choice == 0:
                break
            try:
                menu[choice - 1][1]()
            except (ValueError, DuplicateIdException, DeviceNotReadyException) as ex:
                print("Lỗi:", ex)


if __name__ == "__main__":
    try:
        app = App()
        app.load_sample_data()
        app.run()
    except (KeyboardInterrupt, EOFError):
        print("\nĐã thoát chương trình.")