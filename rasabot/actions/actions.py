from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from actions.parsers.pitch_parser import extract_pitch_name_from_text
from actions.services.pitch_service import get_pitch_by_name
from actions.services.booking_service import is_pitch_available
from actions.services.booking_service import get_available_pitches
from actions.parsers.datetime_parser import extract_booking_datetime_info
from actions.services.branch_service import count_branches, get_branches
from actions.services.pitch_service import get_pitches_by_branch_name
from actions.parsers.branch_parser import (
    extract_branch_name_from_text,
    normalize_branch_name,
    looks_like_branch_query,
    has_branch_like_pattern,
)


class ActionCountBranches(Action):
    def name(self) -> str:
        return "action_count_branches"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        total = count_branches()
        dispatcher.utter_message(text=f"Hệ thống hiện có {total} chi nhánh.")
        return []


class ActionListBranches(Action):
    def name(self) -> str:
        return "action_list_branches"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        branches = get_branches()
        names = [branch[1] for branch in branches]

        if not names:
            dispatcher.utter_message(text="Hiện tại chưa có chi nhánh nào.")
            return []

        dispatcher.utter_message(
            text="Các chi nhánh hiện có: " + ", ".join(names)
        )
        return []


class ActionListPitchesByBranch(Action):
    def name(self) -> str:
        return "action_list_pitches_by_branch"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        latest_text = tracker.latest_message.get("text", "")

        branch_name = extract_branch_name_from_text(latest_text)

        if not branch_name:
            # Nếu có vẻ đang hỏi về sân/chi nhánh nhưng không parse ra branch
            if has_branch_like_pattern(latest_text):
                dispatcher.utter_message(
                    text="Chi nhánh này không tồn tại hoặc bạn ghi tên chi nhánh chưa đúng."
                )
                return []

            if looks_like_branch_query(latest_text):
                dispatcher.utter_message(text="Bạn muốn xem sân ở chi nhánh nào?")
                return []

            dispatcher.utter_message(
                text="Tôi chưa hiểu rõ ý bạn. Bạn có thể hỏi về chi nhánh hoặc sân theo chi nhánh."
            )
            return []

        normalized_branch_name = normalize_branch_name(branch_name)
        pitches = get_pitches_by_branch_name(normalized_branch_name)

        if not pitches:
            dispatcher.utter_message(
                text="Chi nhánh này không tồn tại hoặc bạn ghi tên chi nhánh chưa đúng."
            )
            return []

        pitch_names = [pitch[1] for pitch in pitches]
        dispatcher.utter_message(
            text=f"{normalized_branch_name} có các sân: " + ", ".join(pitch_names)
        )
        return []

class ActionCheckAvailablePitchesByBranch(Action):
    def name(self) -> str:
        return "action_check_available_pitches_by_branch"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        latest_text = tracker.latest_message.get("text", "")

        branch_name = extract_branch_name_from_text(latest_text)
        if not branch_name:
            dispatcher.utter_message(text="Bạn muốn xem sân rảnh ở chi nhánh nào?")
            return []

        normalized_branch_name = normalize_branch_name(branch_name)

        datetime_info = extract_booking_datetime_info(latest_text)
        if not datetime_info["is_complete"]:
            missing_fields = datetime_info["missing_fields"]

            if missing_fields == ["booking_date"]:
                dispatcher.utter_message(text="Bạn vui lòng cung cấp ngày đặt cụ thể.")
                return []

            if missing_fields == ["start_time"]:
                dispatcher.utter_message(text="Bạn vui lòng cung cấp giờ bắt đầu cụ thể.")
                return []

            if missing_fields == ["end_time"]:
                dispatcher.utter_message(text="Bạn vui lòng cung cấp giờ kết thúc cụ thể.")
                return []

            dispatcher.utter_message(
                text="Bạn vui lòng cung cấp ngày đặt, giờ bắt đầu và giờ kết thúc cụ thể."
            )
            return []

        result = get_available_pitches(
            branch_name=normalized_branch_name,
            booking_date=datetime_info["booking_date"],
            start_time=datetime_info["start_time"],
            end_time=datetime_info["end_time"],
        )

        if not result["ok"]:
            dispatcher.utter_message(text=result["message"])
            return []

        pitches = result["data"]
        if not pitches:
            dispatcher.utter_message(
                text=(
                    f"Không có sân trống ở {normalized_branch_name} trong khung giờ "
                    f"{datetime_info['booking_date']} từ {datetime_info['start_time']} đến {datetime_info['end_time']}."
                )
            )
            return []

        pitch_names = [pitch[1] for pitch in pitches]
        dispatcher.utter_message(
            text=(
                f"Các sân còn trống ở {normalized_branch_name} ngày {datetime_info['booking_date']} "
                f"từ {datetime_info['start_time']} đến {datetime_info['end_time']}: "
                + ", ".join(pitch_names)
            )
        )
        return []

class ActionCheckPitchAvailability(Action):
    def name(self) -> str:
        return "action_check_pitch_availability"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        latest_text = tracker.latest_message.get("text", "")

        # 1. parse pitch name
        pitch_name = extract_pitch_name_from_text(latest_text)
        if not pitch_name:
            dispatcher.utter_message(text="Bạn muốn kiểm tra sân nào cụ thể?")
            return []

        # 2. parse datetime
        datetime_info = extract_booking_datetime_info(latest_text)
        if not datetime_info["is_complete"]:
            missing_fields = datetime_info["missing_fields"]

            if missing_fields == ["booking_date"]:
                dispatcher.utter_message(text="Bạn vui lòng cung cấp ngày đặt cụ thể.")
                return []

            if missing_fields == ["start_time"]:
                dispatcher.utter_message(text="Bạn vui lòng cung cấp giờ bắt đầu.")
                return []

            if missing_fields == ["end_time"]:
                dispatcher.utter_message(text="Bạn vui lòng cung cấp giờ kết thúc.")
                return []

            dispatcher.utter_message(
                text="Bạn vui lòng cung cấp ngày, giờ bắt đầu và giờ kết thúc."
            )
            return []

        # 3. tìm pitch trong DB
        pitch = get_pitch_by_name(pitch_name)
        if not pitch:
            dispatcher.utter_message(
                text=f"Không tìm thấy sân '{pitch_name}'. Bạn kiểm tra lại tên giúp tôi."
            )
            return []

        pitch_id = pitch[0]
        pitch_real_name = pitch[1]

        # 4. check availability
        result = is_pitch_available(
            pitch_id=pitch_id,
            booking_date=datetime_info["booking_date"],
            start_time=datetime_info["start_time"],
            end_time=datetime_info["end_time"],
        )

        if not result["ok"]:
            dispatcher.utter_message(text=result["message"])
            return []

        if result["available"]:
            dispatcher.utter_message(
                text=(
                    f"{pitch_real_name} còn trống từ {datetime_info['start_time']} "
                    f"đến {datetime_info['end_time']} ngày {datetime_info['booking_date']}."
                )
            )
        else:
            dispatcher.utter_message(
                text=(
                    f"{pitch_real_name} đã được đặt trong khung giờ "
                    f"{datetime_info['start_time']} đến {datetime_info['end_time']} "
                    f"ngày {datetime_info['booking_date']}."
                )
            )

        return []