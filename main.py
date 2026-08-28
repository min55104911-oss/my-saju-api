from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from lunar_python import Solar

app = FastAPI(
    title="맑은눈 묘월도사 만세력 API",
    version="2.0.0"
)


class SajuRequest(BaseModel):
    year: int
    month: int
    day: int
    time: str
    gender: str
    birthplace: str


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "my-saju-api",
        "version": "2.0"
    }


@app.post("/calculateSajuChart")
def calculate_saju_chart(data: SajuRequest):
    try:
        # -------------------------
        # 1. 입력값 처리
        # -------------------------
        hour, minute = map(int, data.time.split(":"))

        if not (0 <= hour <= 23):
            raise ValueError("출생 시간(hour)은 0~23이어야 합니다.")

        if not (0 <= minute <= 59):
            raise ValueError("출생 분(minute)은 0~59이어야 합니다.")

        gender_text = data.gender.strip().lower()

        if gender_text in ["male", "m", "남", "남자", "남성"]:
            gender_code = 1
            gender_normalized = "male"
        elif gender_text in ["female", "f", "여", "여자", "여성"]:
            gender_code = 0
            gender_normalized = "female"
        else:
            raise ValueError("gender는 male 또는 female이어야 합니다.")

        # -------------------------
        # 2. 양력 → 만세력
        # -------------------------
        solar = Solar.fromYmdHms(
            data.year,
            data.month,
            data.day,
            hour,
            minute,
            0
        )

        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        # -------------------------
        # 3. 사주 원국
        # -------------------------
        pillars = {
            "year": eight_char.getYear(),
            "month": eight_char.getMonth(),
            "day": eight_char.getDay(),
            "hour": eight_char.getTime()
        }

        chart = {
            "yearPillar": pillars["year"],
            "monthPillar": pillars["month"],
            "dayPillar": pillars["day"],
            "hourPillar": pillars["hour"]
        }

        # -------------------------
        # 4. 대운
        # -------------------------
        yun = eight_char.getYun(gender_code)

        direction = "forward" if yun.isForward() else "backward"
        direction_ko = "순행" if yun.isForward() else "역행"

        start_solar = yun.getStartSolar()

        luck_cycles = []

        for da_yun in yun.getDaYun():
            luck_cycles.append({
                "index": da_yun.getIndex(),
                "ganZhi": da_yun.getGanZhi(),
                "startYear": da_yun.getStartYear(),
                "endYear": da_yun.getEndYear(),
                "startAge": da_yun.getStartAge(),
                "endAge": da_yun.getEndAge()
            })

        # -------------------------
        # 5. 계산 정책
        # -------------------------
        calculation_policy = {
            "calendar": "solar",
            "calendarDescription": "현재 API 입력 생년월일은 양력 기준",
            "timezone": "input-local-time",
            "birthplaceUsedForTimezoneCorrection": False,
            "trueSolarTimeCorrection": False,
            "dayBoundaryPolicy": "lunar-python default",
            "luckMethod": "lunar-python EightChar.getYun default sect=1",
            "genderRule": "male=1, female=0"
        }

        warnings = [
            "현재 버전은 입력된 출생 시각을 그대로 사용합니다.",
            "출생지에 따른 경도 보정 및 진태양시 보정은 아직 적용하지 않습니다.",
            "현재 생년월일 입력은 양력 기준입니다.",
            "음력 및 윤달 입력은 별도 변환 기능 추가 전까지 직접 입력하지 마세요."
        ]

        return {
            "ok": True,

            "input": {
                "year": data.year,
                "month": data.month,
                "day": data.day,
                "time": data.time,
                "gender": gender_normalized,
                "birthplace": data.birthplace
            },

            "pillars": pillars,

            # 기존 GPT/Worker 호환용
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

            "calculation_policy": calculation_policy,

            "warnings": warnings
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
