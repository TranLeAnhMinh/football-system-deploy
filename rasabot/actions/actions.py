from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.services.booking_service import get_available_slots_in_time_range_for_pitch
from actions.services.booking_service import get_nearest_available_slots_for_pitch
from actions.services.booking_service import is_valid_slot_boundary
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


SUPPORTED_LANGS = ["vi", "en", "ja"]


MESSAGES = {
    "missing_booking_date_start_time": {
    "vi": "Bạn vui lòng cung cấp ngày đặt và giờ bắt đầu cụ thể.",
    "en": "Please provide the booking date and start time.",
    "ja": "予約日と開始時間を入力してください。",
},
"missing_booking_date_end_time": {
    "vi": "Bạn vui lòng cung cấp ngày đặt và giờ kết thúc cụ thể.",
    "en": "Please provide the booking date and end time.",
    "ja": "予約日と終了時間を入力してください。",
},
"missing_start_end_time": {
    "vi": "Bạn vui lòng cung cấp giờ bắt đầu và giờ kết thúc cụ thể.",
    "en": "Please provide the start time and end time.",
    "ja": "開始時間と終了時間を入力してください。",
},
"invalid_booking_date": {
    "vi": "Ngày đặt không hợp lệ. Vui lòng nhập theo định dạng YYYY-MM-DD.",
    "en": "The booking date is invalid. Please use the YYYY-MM-DD format.",
    "ja": "予約日が無効です。YYYY-MM-DD形式で入力してください。",
},
"invalid_start_time_format": {
    "vi": "Giờ bắt đầu không hợp lệ. Vui lòng nhập theo định dạng HH:MM.",
    "en": "The start time is invalid. Please use the HH:MM format.",
    "ja": "開始時間が無効です。HH:MM形式で入力してください。",
},
"invalid_end_time_format": {
    "vi": "Giờ kết thúc không hợp lệ. Vui lòng nhập theo định dạng HH:MM.",
    "en": "The end time is invalid. Please use the HH:MM format.",
    "ja": "終了時間が無効です。HH:MM形式で入力してください。",
},
"invalid_start_slot_boundary": {
    "vi": "Giờ bắt đầu không hợp lệ. Hệ thống dùng slot 45 phút tính từ 00:00. Ví dụ hợp lệ: 00:00, 00:45, 01:30.",
    "en": "The start time is invalid. The system uses 45-minute slots starting from 00:00. Valid examples: 00:00, 00:45, 01:30.",
    "ja": "開始時間が無効です。システムは00:00から45分単位の枠を使用します。有効な例: 00:00、00:45、01:30。",
},
"invalid_end_slot_boundary": {
    "vi": "Giờ kết thúc không hợp lệ. Hệ thống dùng slot 45 phút tính từ 00:00. Ví dụ hợp lệ: 00:00, 00:45, 01:30.",
    "en": "The end time is invalid. The system uses 45-minute slots starting from 00:00. Valid examples: 00:00, 00:45, 01:30.",
    "ja": "終了時間が無効です。システムは00:00から45分単位の枠を使用します。有効な例: 00:00、00:45、01:30。",
},
"invalid_time_range": {
    "vi": "Khung giờ không hợp lệ. Giờ kết thúc phải lớn hơn giờ bắt đầu và khoảng thời gian phải theo bội số 45 phút.",
    "en": "The time range is invalid. The end time must be later than the start time, and the duration must be a multiple of 45 minutes.",
    "ja": "時間帯が無効です。終了時間は開始時間より後で、時間の長さは45分の倍数である必要があります。",
},
"invalid_branch_name": {
    "vi": "Bạn vui lòng cung cấp tên chi nhánh hợp lệ.",
    "en": "Please provide a valid branch name.",
    "ja": "有効な店舗名を入力してください。",
},
"database_error": {
    "vi": "Đã xảy ra lỗi khi truy vấn dữ liệu. Bạn vui lòng thử lại sau.",
    "en": "An error occurred while querying data. Please try again later.",
    "ja": "データの取得中にエラーが発生しました。後でもう一度お試しください。",
},
    "branch_count": {
        "vi": "Hệ thống hiện có {total} chi nhánh.",
        "en": "The system currently has {total} branches.",
        "ja": "システムには現在{total}店舗があります。",
    },
    "no_branches": {
        "vi": "Hiện tại chưa có chi nhánh nào.",
        "en": "There are currently no branches.",
        "ja": "現在、店舗はありません。",
    },
    "branch_list": {
        "vi": "Các chi nhánh hiện có: {names}",
        "en": "Available branches: {names}",
        "ja": "現在利用可能な店舗: {names}",
    },
    "branch_not_found": {
        "vi": "Chi nhánh này không tồn tại hoặc bạn ghi tên chi nhánh chưa đúng.",
        "en": "This branch does not exist, or the branch name may be incorrect.",
        "ja": "この店舗は存在しないか、店舗名が正しくありません。",
    },
    "ask_branch_name": {
        "vi": "Bạn muốn xem sân ở chi nhánh nào?",
        "en": "Which branch would you like to view pitches from?",
        "ja": "どの店舗のサッカー場を確認しますか？",
    },
    "fallback_branch": {
        "vi": "Tôi chưa hiểu rõ ý bạn. Bạn có thể hỏi về chi nhánh hoặc sân theo chi nhánh.",
        "en": "I did not understand clearly. You can ask about branches or pitches by branch.",
        "ja": "内容を正しく理解できませんでした。店舗または店舗ごとのサッカー場について質問できます。",
    },
    "pitches_by_branch": {
        "vi": "{branch_name} có các sân: {pitch_names}",
        "en": "{branch_name} has the following pitches: {pitch_names}",
        "ja": "{branch_name}には次のサッカー場があります: {pitch_names}",
    },
    "ask_available_branch": {
        "vi": "Bạn muốn xem sân rảnh ở chi nhánh nào?",
        "en": "Which branch would you like to check available pitches from?",
        "ja": "どの店舗の空きサッカー場を確認しますか？",
    },
    "missing_booking_date": {
        "vi": "Bạn vui lòng cung cấp ngày đặt cụ thể.",
        "en": "Please provide a specific booking date.",
        "ja": "予約日を具体的に入力してください。",
    },
    "missing_start_time": {
        "vi": "Bạn vui lòng cung cấp giờ bắt đầu cụ thể.",
        "en": "Please provide a specific start time.",
        "ja": "開始時間を具体的に入力してください。",
    },
    "missing_end_time": {
        "vi": "Bạn vui lòng cung cấp giờ kết thúc cụ thể.",
        "en": "Please provide a specific end time.",
        "ja": "終了時間を具体的に入力してください。",
    },
    "missing_datetime": {
        "vi": "Bạn vui lòng cung cấp ngày đặt, giờ bắt đầu và giờ kết thúc cụ thể.",
        "en": "Please provide the booking date, start time, and end time.",
        "ja": "予約日、開始時間、終了時間を入力してください。",
    },
    "past_time": {
        "vi": "Thời gian bạn nhập đã ở trong quá khứ. Hệ thống chỉ hỗ trợ kiểm tra sân cho thời gian hiện tại hoặc tương lai.",
        "en": "The time you entered is in the past. The system only supports checking pitches for the current or future time.",
        "ja": "入力された時間は過去の時間です。現在または未来の時間のみ確認できます。",
    },
    "no_available_pitches": {
        "vi": "Không có sân trống ở {branch_name} trong khung giờ {booking_date} từ {start_time} đến {end_time}.",
        "en": "There are no available pitches at {branch_name} on {booking_date} from {start_time} to {end_time}.",
        "ja": "{branch_name}では、{booking_date}の{start_time}から{end_time}まで空いているサッカー場はありません。",
    },
    "available_pitches": {
        "vi": "Các sân còn trống ở {branch_name} ngày {booking_date} từ {start_time} đến {end_time}: {pitch_names}",
        "en": "Available pitches at {branch_name} on {booking_date} from {start_time} to {end_time}: {pitch_names}",
        "ja": "{branch_name}で{booking_date}の{start_time}から{end_time}まで空いているサッカー場: {pitch_names}",
    },
    "ask_pitch_name": {
        "vi": "Bạn muốn kiểm tra sân nào cụ thể?",
        "en": "Which specific pitch would you like to check?",
        "ja": "どのサッカー場を確認しますか？",
    },
    "missing_datetime_pitch": {
        "vi": "Bạn vui lòng cung cấp ngày, giờ bắt đầu và giờ kết thúc.",
        "en": "Please provide the date, start time, and end time.",
        "ja": "日付、開始時間、終了時間を入力してください。",
    },
    "pitch_not_found": {
        "vi": "Không tìm thấy sân '{pitch_name}'. Bạn kiểm tra lại tên giúp tôi.",
        "en": "Could not find the pitch '{pitch_name}'. Please check the name again.",
        "ja": "サッカー場「{pitch_name}」が見つかりません。名前を確認してください。",
    },
    "pitch_available": {
        "vi": "{pitch_name} còn trống từ {start_time} đến {end_time} ngày {booking_date}.",
        "en": "{pitch_name} is available from {start_time} to {end_time} on {booking_date}.",
        "ja": "{pitch_name}は{booking_date}の{start_time}から{end_time}まで空いています。",
    },
    "pitch_unavailable": {
        "vi": "{pitch_name} đã được đặt hoặc bảo trì trong khung giờ {start_time} đến {end_time} ngày {booking_date}.",
        "en": "{pitch_name} has already been booked or is under maintenance from {start_time} to {end_time} on {booking_date}.",
        "ja": "{pitch_name}は{booking_date}の{start_time}から{end_time}まで予約済み、またはメンテナンス中です。",
    },
    "booking_guide": {
        "vi": "Ở màn hình chính, bạn có thể chọn loại sân bạn muốn đặt, sau đó chọn sân mong muốn và tiến hành đặt sân. Trước khi đặt, bạn có thể xem trước các khung giờ đặt sân ở calendar.",
        "en": "On the home screen, you can choose the type of pitch you want to book, then select your preferred pitch and proceed with the booking. Before booking, you can preview the available time slots in the calendar.",
        "ja": "ホーム画面で予約したいサッカー場の種類を選択し、希望するサッカー場を選んで予約できます。予約前にカレンダーで予約可能な時間帯を確認できます。",
    },
}


def get_language(tracker: Tracker) -> str:
    metadata = tracker.latest_message.get("metadata") or {}
    language = metadata.get("language") or "vi"

    if language not in SUPPORTED_LANGS:
        return "vi"

    return language


def msg(tracker: Tracker, key: str, **kwargs) -> str:
    language = get_language(tracker)
    template = MESSAGES.get(key, {}).get(language) or MESSAGES.get(key, {}).get("vi", "")
    return template.format(**kwargs)


class ActionCountBranches(Action):
    def name(self) -> str:
        return "action_count_branches"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        total = count_branches()
        dispatcher.utter_message(text=msg(tracker, "branch_count", total=total))
        return []


class ActionListBranches(Action):
    def name(self) -> str:
        return "action_list_branches"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        branches = get_branches()
        names = [branch[1] for branch in branches]

        if not names:
            dispatcher.utter_message(text=msg(tracker, "no_branches"))
            return []

        dispatcher.utter_message(
            text=msg(tracker, "branch_list", names=", ".join(names))
        )
        return []

class ActionGreet(Action):
    def name(self) -> str:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        messages = {
            "vi": "Chào bạn, tôi có thể hướng dẫn bạn cách đặt sân, xem chi nhánh, danh sách sân, sân theo từng chi nhánh và tra cứu giờ trống của sân.",
            "en": "Hello, I can guide you on how to book a pitch, view branches, view the pitch list, view pitches by branch, and check available time slots.",
            "ja": "こんにちは。予約方法、支店一覧、サッカー場一覧、支店ごとのサッカー場、空き時間の確認についてご案内できます。"
        }

        dispatcher.utter_message(
            text=messages.get(get_language(tracker), messages["vi"])
        )
        return []


class ActionGoodbye(Action):
    def name(self) -> str:
        return "action_goodbye"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        messages = {
            "vi": "Tạm biệt bạn nhé. Khi nào cần giúp đỡ thì cứ nhắn tôi.",
            "en": "Goodbye. Feel free to message me whenever you need help.",
            "ja": "さようなら。また必要なときはいつでもメッセージしてください。"
        }

        dispatcher.utter_message(
            text=messages.get(get_language(tracker), messages["vi"])
        )
        return []


class ActionFallback(Action):
    def name(self) -> str:
        return "action_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        dispatcher.utter_message(text=msg(tracker, "fallback_branch"))
        return []

class ActionListPitchesByBranch(Action):
    def name(self) -> str:
        return "action_list_pitches_by_branch"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        latest_text = tracker.latest_message.get("text", "")

        branch_name = extract_branch_name_from_text(latest_text)

        if not branch_name:
            if has_branch_like_pattern(latest_text):
                dispatcher.utter_message(text=msg(tracker, "branch_not_found"))
                return []

            if looks_like_branch_query(latest_text):
                dispatcher.utter_message(text=msg(tracker, "ask_branch_name"))
                return []

            dispatcher.utter_message(text=msg(tracker, "fallback_branch"))
            return []

        normalized_branch_name = normalize_branch_name(branch_name)
        pitches = get_pitches_by_branch_name(normalized_branch_name)

        if not pitches:
            dispatcher.utter_message(text=msg(tracker, "branch_not_found"))
            return []

        pitch_names = [pitch[1] for pitch in pitches]
        dispatcher.utter_message(
            text=msg(
                tracker,
                "pitches_by_branch",
                branch_name=normalized_branch_name,
                pitch_names=", ".join(pitch_names),
            )
        )
        return []


class ActionCheckAvailablePitchesByBranch(Action):
    def name(self) -> str:
        return "action_check_available_pitches_by_branch"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        latest_text = tracker.latest_message.get("text", "")

        pitch_name = extract_pitch_name_from_text(latest_text)
        if pitch_name:
            return ActionCheckPitchAvailability().run(dispatcher, tracker, domain)

        branch_name = extract_branch_name_from_text(latest_text)
        if not branch_name:
            dispatcher.utter_message(text=msg(tracker, "ask_available_branch"))
            return []

        normalized_branch_name = normalize_branch_name(branch_name)

        datetime_info = extract_booking_datetime_info(latest_text)
        if not datetime_info["is_complete"]:
            missing_fields = datetime_info["missing_fields"]

            if missing_fields == ["booking_date"]:
                dispatcher.utter_message(text=msg(tracker, "missing_booking_date"))
                return []

            if missing_fields == ["start_time"]:
                dispatcher.utter_message(text=msg(tracker, "missing_start_time"))
                return []

            if missing_fields == ["end_time"]:
                dispatcher.utter_message(text=msg(tracker, "missing_end_time"))
                return []

            dispatcher.utter_message(text=msg(tracker, "missing_datetime"))
            return []

        if datetime_info.get("is_past"):
            dispatcher.utter_message(text=msg(tracker, "past_time"))
            return []

        booking_date = datetime_info["booking_date"]
        start_time = datetime_info["start_time"]
        end_time = datetime_info["end_time"]

        # Nếu người dùng hỏi theo chi nhánh nhưng giờ không đúng slot 45 phút,
        # bot sẽ gợi ý các khung giờ trống theo từng sân trong chi nhánh.
        if not is_valid_slot_boundary(start_time) or not is_valid_slot_boundary(end_time):
            pitches = get_pitches_by_branch_name(normalized_branch_name)

            if not pitches:
                dispatcher.utter_message(text=msg(tracker, "branch_not_found"))
                return []

            response_lines = []
            rounded_start_time = None
            rounded_end_time = None

            for pitch in pitches:
                pitch_id = pitch[0]
                pitch_name = pitch[1]

                result = get_available_slots_in_time_range_for_pitch(
                    pitch_id=pitch_id,
                    booking_date=booking_date,
                    requested_start_time=start_time,
                    requested_end_time=end_time,
                )

                if not result["ok"]:
                    dispatcher.utter_message(text=msg(tracker, result["error_key"]))
                    return []

                rounded_start_time = result["rounded_start_time"]
                rounded_end_time = result["rounded_end_time"]

                slots = result["data"]
                if not slots:
                    continue

                slot_text = ", ".join(
                    [
                        f"{slot['start_time']} đến {slot['end_time']}"
                        for slot in slots
                    ]
                )

                response_lines.append(f"- {pitch_name}: {slot_text}")

            if not response_lines:
                dispatcher.utter_message(
                    text=(
                        f"Hệ thống đặt sân theo slot 45 phút.\n"
                        f"Khung giờ bạn nhập ({start_time} đến {end_time}) không đúng slot hợp lệ.\n\n"
                        f"Khung giờ hợp lệ gần nhất là {rounded_start_time} đến {rounded_end_time}.\n"
                        f"Hiện không có sân trống ở {normalized_branch_name} trong khung giờ này."
                    )
                )
                return []

            dispatcher.utter_message(
                text=(
                    f"Hệ thống đặt sân theo slot 45 phút.\n"
                    f"Khung giờ bạn nhập ({start_time} đến {end_time}) không đúng slot hợp lệ.\n\n"
                    f"Khung giờ hợp lệ gần nhất là {rounded_start_time} đến {rounded_end_time}.\n"
                    f"Các sân trống ở {normalized_branch_name} ngày {booking_date} là:\n"
                    + "\n".join(response_lines)
                )
            )
            return []

        result = get_available_pitches(
            branch_name=normalized_branch_name,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
        )

        if not result["ok"]:
            dispatcher.utter_message(text=msg(tracker, result["error_key"]))
            return []

        pitches = result["data"]
        if not pitches:
            dispatcher.utter_message(
                text=msg(
                    tracker,
                    "no_available_pitches",
                    branch_name=normalized_branch_name,
                    booking_date=booking_date,
                    start_time=start_time,
                    end_time=end_time,
                )
            )
            return []

        pitch_names = [pitch[1] for pitch in pitches]
        dispatcher.utter_message(
            text=msg(
                tracker,
                "available_pitches",
                branch_name=normalized_branch_name,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_time,
                pitch_names=", ".join(pitch_names),
            )
        )
        return []


class ActionCheckPitchAvailability(Action):
    def name(self) -> str:
        return "action_check_pitch_availability"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        latest_text = tracker.latest_message.get("text", "")

        branch_name = extract_branch_name_from_text(latest_text)
        pitch_name = extract_pitch_name_from_text(latest_text)

        # Nếu NLU đoán nhầm sang check sân cụ thể,
        # nhưng câu thực tế là hỏi theo chi nhánh,
        # thì chuyển về action check sân theo chi nhánh.
        if branch_name and not pitch_name:
            return ActionCheckAvailablePitchesByBranch().run(
                dispatcher,
                tracker,
                domain,
            )

        if not pitch_name:
            dispatcher.utter_message(text=msg(tracker, "ask_pitch_name"))
            return []

        datetime_info = extract_booking_datetime_info(latest_text)

        if not datetime_info["is_complete"]:
            last_booking_date = tracker.get_slot("last_booking_date")
            last_start_time = tracker.get_slot("last_start_time")
            last_end_time = tracker.get_slot("last_end_time")

            if last_booking_date and last_start_time and last_end_time:
                datetime_info = {
                    "booking_date": last_booking_date,
                    "start_time": last_start_time,
                    "end_time": last_end_time,
                    "missing_fields": [],
                    "is_complete": True,
                    "is_past": False,
                }

        if not datetime_info["is_complete"]:
            missing_fields = datetime_info["missing_fields"]

            if missing_fields == ["booking_date"]:
                dispatcher.utter_message(text=msg(tracker, "missing_booking_date"))
                return []

            if missing_fields == ["start_time"]:
                dispatcher.utter_message(text=msg(tracker, "missing_start_time"))
                return []

            if missing_fields == ["end_time"]:
                dispatcher.utter_message(text=msg(tracker, "missing_end_time"))
                return []

            dispatcher.utter_message(text=msg(tracker, "missing_datetime_pitch"))
            return []

        if datetime_info.get("is_past"):
            dispatcher.utter_message(text=msg(tracker, "past_time"))
            return []

        pitch = get_pitch_by_name(pitch_name)
        if not pitch:
            dispatcher.utter_message(
                text=msg(tracker, "pitch_not_found", pitch_name=pitch_name)
            )
            return []

        pitch_id = pitch[0]
        pitch_real_name = pitch[1]

        booking_date = datetime_info["booking_date"]
        start_time = datetime_info["start_time"]
        end_time = datetime_info["end_time"]

        slot_events = [
            SlotSet("last_pitch_name", pitch_real_name),
            SlotSet("last_booking_date", booking_date),
            SlotSet("last_start_time", start_time),
            SlotSet("last_end_time", end_time),
        ]

        if not is_valid_slot_boundary(start_time) or not is_valid_slot_boundary(end_time):
            result = get_available_slots_in_time_range_for_pitch(
                pitch_id=pitch_id,
                booking_date=booking_date,
                requested_start_time=start_time,
                requested_end_time=end_time,
            )

            if not result["ok"]:
                dispatcher.utter_message(text=msg(tracker, result["error_key"]))
                return []

            slots = result["data"]
            rounded_start_time = result["rounded_start_time"]
            rounded_end_time = result["rounded_end_time"]

            if not slots:
                dispatcher.utter_message(
                    text=(
                        f"Hệ thống đặt sân theo slot 45 phút.\n"
                        f"Khung giờ bạn nhập ({start_time} đến {end_time}) không đúng slot hợp lệ.\n\n"
                        f"Khung giờ hợp lệ gần nhất là {rounded_start_time} đến {rounded_end_time}.\n"
                        f"Tuy nhiên hiện chưa có khung giờ trống cho {pitch_real_name} ngày {booking_date}."
                    )
                )
                return slot_events

            slot_text = "\n".join(
                [
                    f"- {slot['start_time']} đến {slot['end_time']}"
                    for slot in slots
                ]
            )

            dispatcher.utter_message(
                text=(
                    f"Hệ thống đặt sân theo slot 45 phút.\n"
                    f"Khung giờ bạn nhập ({start_time} đến {end_time}) không đúng slot hợp lệ.\n\n"
                    f"Khung giờ hợp lệ gần nhất là {rounded_start_time} đến {rounded_end_time}.\n"
                    f"Các khung giờ trống của {pitch_real_name} ngày {booking_date} là:\n"
                    f"{slot_text}"
                )
            )
            return slot_events

        result = is_pitch_available(
            pitch_id=pitch_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
        )

        if not result["ok"]:
            dispatcher.utter_message(text=msg(tracker, result["error_key"]))
            return []

        if result["available"]:
            dispatcher.utter_message(
                text=msg(
                    tracker,
                    "pitch_available",
                    pitch_name=pitch_real_name,
                    start_time=start_time,
                    end_time=end_time,
                    booking_date=booking_date,
                )
            )
        else:
            dispatcher.utter_message(
                text=msg(
                    tracker,
                    "pitch_unavailable",
                    pitch_name=pitch_real_name,
                    start_time=start_time,
                    end_time=end_time,
                    booking_date=booking_date,
                )
            )

        return slot_events

class ActionBookingGuide(Action):
    def name(self) -> str:
        return "action_booking_guide"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        dispatcher.utter_message(text=msg(tracker, "booking_guide"))
        return []