import { Lunar, Solar } from 'lunar-typescript'

// The library supports multiple calculation "sects" (variant conventions).
export type Sect = 1 | 2

export type BirthInput = {
    year: number
    month: number // 1-12
    day: number // 1-31
    hour: number // 0-23
    minute?: number // 0-59
    second?: number // 0-59
}

export type Pillar = {
    gan: string
    zhi: string
    ganZhi: string
}

export type BaziResult = {
    sect: Sect
    pillars: {
        year: Pillar
        month: Pillar
        day: Pillar
        hour: Pillar
    }
    // “Exactly what we calculated” (raw arrays from the engine):
    baZi: string[]          // 八字 (8 chars)
    baZiWuXing: string[]    // 五行 for the 8 chars
    shiShenGan: string[]    // 十神 for heavenly stems
    shiShenZhi: string[]    // 十神 for earthly branches
}

export type NineStarInfo = {
    number: string
    color: string
    element: string
    position: string
    nameXuanKong: string
    nameBeiDou: string
    nameQiMen: string
}

export type NineStarResult = {
    sect: Sect
    year: NineStarInfo
    month: NineStarInfo
    // Optional but useful to show now for verification/debug:
    day: NineStarInfo
    time: NineStarInfo
}

export type BirthProfileResult = {
    sect: Sect
    input: BirthInput
    bazi: BaziResult
    nineStar: NineStarResult
    // Useful debug strings:
    lunarString: string
}

export function parseDatetimeLocal(datetimeLocal: string): BirthInput {
    // Accepts "YYYY-MM-DDTHH:mm" or "YYYY-MM-DDTHH:mm:ss"
    const [d, tRaw] = datetimeLocal.split('T')
    if (!d || !tRaw) throw new Error('Invalid datetime-local value')

    const dateParts = d.split('-').map((x) => Number(x))
    if (dateParts.length < 3) throw new Error('Invalid date format')
    
    const year = dateParts[0]!
    const month = dateParts[1]!
    const day = dateParts[2]!
    
    const tParts = tRaw.split(':').map((x) => Number(x))
    if (tParts.length < 2) throw new Error('Invalid time format')
    
    const hour = tParts[0]!
    const minute = tParts[1] ?? 0
    const second = tParts[2] ?? 0

    if (![year, month, day, hour, minute, second].every((n) => Number.isFinite(n))) {
        throw new Error('Invalid datetime-local numeric parts')
    }

    return { year, month, day, hour, minute, second }
}

function nineStarToInfo(ns: any): NineStarInfo {
    return {
        number: ns.getNumber(),
        color: ns.getColor(),
        element: ns.getWuXing(),
        position: ns.getPosition(),
        nameXuanKong: ns.getNameInXuanKong(),
        nameBeiDou: ns.getNameInBeiDou(),
        nameQiMen: ns.getNameInQiMen(),
    }
}

export function computeBirthProfile(input: BirthInput, sect: Sect = 2): BirthProfileResult {
    const solar = Solar.fromYmdHms(
        input.year,
        input.month,
        input.day,
        input.hour,
        input.minute ?? 0,
        input.second ?? 0
    )
    const lunar = Lunar.fromSolar(solar)

    // BaZi (EightChar)
    const eightChar = lunar.getEightChar()
    eightChar.setSect(sect)

    const bazi: BaziResult = {
        sect,
        pillars: {
            year: { gan: eightChar.getYearGan(), zhi: eightChar.getYearZhi(), ganZhi: eightChar.getYear() },
            month: { gan: eightChar.getMonthGan(), zhi: eightChar.getMonthZhi(), ganZhi: eightChar.getMonth() },
            day: { gan: eightChar.getDayGan(), zhi: eightChar.getDayZhi(), ganZhi: eightChar.getDay() },
            hour: { gan: eightChar.getTimeGan(), zhi: eightChar.getTimeZhi(), ganZhi: eightChar.getTime() },
        },
        baZi: lunar.getBaZi(),
        baZiWuXing: lunar.getBaZiWuXing(),
        shiShenGan: lunar.getBaZiShiShenGan(),
        shiShenZhi: lunar.getBaZiShiShenZhi(),
    }

    // Nine Star (Year/Month are the key “Nine Star Ki” primitives)
    const nineStar: NineStarResult = {
        sect,
        year: nineStarToInfo(lunar.getYearNineStar(sect)),
        month: nineStarToInfo(lunar.getMonthNineStar(sect)),
        day: nineStarToInfo(lunar.getDayNineStar()),
        time: nineStarToInfo(lunar.getTimeNineStar()),
    }

    return {
        sect,
        input,
        bazi,
        nineStar,
        lunarString: lunar.toString(),
    }
}