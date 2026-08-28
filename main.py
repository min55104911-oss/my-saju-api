from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from lunar_python import Solar, Lunar

app = FastAPI(
    title="맑은눈 묘월도사 만세력 API",
    version="3.0.0"
)


class SajuRequest(BaseModel):
    year: int
    month: int
    day: int
    time: str
    gender: str
    birthplace: str

    # solar = 양력 / lunar = 음력
    calendarType: str = "solar"

    # 음력일 때만 사용
    # 평달 false / 윤달 true
    isLeapMonth: Optional[bool] = False


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "my-saju-api",
        "version": "3.0"
    }


@app.post("/calculateSajuChart")
def calculate_saju_chart(data: SajuRequest):

    try:
        # --------------------------------
        # 1. 시간 검사
        # --------------------------------
        hour, minute = map(int, data.time.split(":"))

        if not 0 <= hour <= 23:
            raise ValueError("출생 시간은 00~23시 사이여야 합니다.")

        if not 0 <= minute <= 59:
            raise ValueError("출생 분은 00~59분 사이여야 합니다.")


        # --------------------------------
        # 2. 성별 처리
        # --------------------------------
        gender_text = data.gender.strip().lower()

        if gender_text in [
            "male", "m", "남", "남자", "남성"
        ]:
            gender_code = 1
            gender_normalized = "male"

        elif gender_text in [
            "female", "f", "여", "여자", "여성"
        ]:
            gender_code = 0
            gender_normalized = "female"

        else:
            raise ValueError(
                "gender는 male 또는 female이어야 합니다."
            )


        # --------------------------------
        # 3. 양력 / 음력 처리
        # --------------------------------
        calendar_type = data.calendarType.strip().lower()

        if calendar_type in [
            "solar", "양력"
        ]:

            solar = Solar.fromYmdHms(
                data.year,
                data.month,
                data.day,
                hour,
                minute,
                0
            )

            lunar = solar.getLunar()

            calendar_normalized = "solar"


        elif calendar_type in [
            "lunar", "음력"
        ]:

            lunar_month = data.month

            # lunar-python은 윤달을 음수 월로 처리
            if data.isLeapMonth:
                lunar_month = -abs(data.month)

            lunar = Lunar.fromYmdHms(
                data.year,
                lunar_month,
                data.day,
                hour,
                minute,
                0
            )

            solar = lunar.getSolar()

            calendar_normalized = "lunar"


        else:
            raise ValueError(
                "calendarType은 solar 또는 lunar이어야 합니다."
            )


        # --------------------------------
        # 4. 사주 원국
        # --------------------------------
        eight_char = lunar.getEightChar()

        pillars = {
            "year": eight_char.getYear(),
            "month": eight_char.getMonth(),
            "day": eight_char.getDay(),
            "hour": eight_char.getTime()
        }

        # 기존 GPT/Worker 호환
        chart = {
            "yearPillar": pillars["year"],
            "monthPillar": pillars["month"],
            "dayPillar": pillars["day"],
            "hourPillar": pillars["hour"]
        }


        # --------------------------------
        # 5. 대운
        # --------------------------------
        yun = eight_char.getYun(gender_code)

        is_forward = yun.isForward()

        direction = (
            "forward"
            if is_forward
            else "backward"
        )

        direction_ko = (
            "순행"
            if is_forward
            else "역행"
        )

        start_solar = yun.getStartSolar()

        luck_cycles = []

        for da_yun in yun.getDaYun():

            # index 0은 출생~기운 전 구간이므로
            # 대운 목록에서는 제외
            if da_yun.getIndex() == 0:
                continue

            luck_cycles.append({
                "index": da_yun.getIndex(),
                "ganZhi": da_yun.getGanZhi(),
                "startYear": da_yun.getStartYear(),
                "endYear": da_yun.getEndYear(),
                "startAge": da_yun.getStartAge(),
                "endAge": da_yun.getEndAge()
            })


        # --------------------------------
        # 6. 실제 사용된 날짜 정보
        # --------------------------------
        converted_dates = {
            "solar": {
                "year": solar.getYear(),
                "month": solar.getMonth(),
                "day": solar.getDay(),
                "time": data.time,
                "date": solar.toYmd()
            },

            "lunar": {
                "year": lunar.getYear(),
                "month": abs(lunar.getMonth()),
                "day": lunar.getDay(),
                "time": data.time,
                "isLeapMonth": lunar.getMonth() < 0
            }
        }


        # --------------------------------
        # 7. 계산 정책
        # --------------------------------
        calculation_policy = {

            "calendarInput": calendar_normalized,

            "calendarConversion":
                "lunar-python",

            "lunarLeapMonthRule":
                "윤달 입력 시 음수 월을 사용하여 lunar-python에서 변환",

            "timezone":
                "input-local-time",

            "birthplaceUsedForTimezoneCorrection":
                False,

            "trueSolarTimeCorrection":
                False,

            "dayBoundaryPolicy":
                "lunar-python default",

            "luckMethod":
                "lunar-python EightChar.getYun default sect=1",

            "genderRule":
                "male=1, female=0"
        }


        # --------------------------------
        # 8. 경고
        # --------------------------------
        warnings = [

            "현재 출생 시각은 입력값을 그대로 사용합니다.",

            "출생지는 기록하지만 경도 보정에는 아직 사용하지 않습니다.",

            "진태양시 보정은 현재 적용하지 않습니다."
        ]


        # --------------------------------
        # 9. 최종 반환
        # --------------------------------
        return {

            "ok": True,

            "input": {
                "year": data.year,
                "month": data.month,
                "day": data.day,
                "time": data.time,
                "gender": gender_normalized,
                "birthplace": data.birthplace,
                "calendarType": calendar_normalized,
                "isLeapMonth": (
                    bool(data.isLeapMonth)
                    if calendar_normalized == "lunar"
                    else False
                )
            },

            "convertedDates": converted_dates,

            "pillars": pillars,

            "chart": chart,

            "luck": {

                "direction": direction,

                "directionKo": direction_ko,

                "start": {
                    "years": yun.getStartYear(),
                    "months": yun.getStartMonth(),
                    "days": yun.getStartDay(),
                    "hours": yun.getStartHour(),
                    "solarDate": start_solar.toYmd()
                },

                "cycles": luck_cycles
            },

            "calculation_policy":
                calculation_policy,

            "warnings":
                warnings
        }


    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
