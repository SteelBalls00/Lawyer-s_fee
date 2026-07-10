# -*- coding: utf-8 -*-
"""Сериализация AppState в JSON-совместимый словарь и обратно.

Используется архивом постановлений: снапшот пишется в БД при сохранении
и восстанавливается при выборе записи из архива.

Два режима восстановления:
- "full"    — полное восстановление (клик по записи архива, без обращения к БД дел);
- "overlay" — наложение поверх свежезагруженного дела (кнопка «Выбрать»):
              списки подсудимых/адвокатов/событий остаются свежими из БД,
              а пользовательские правки и выборы накладываются сверху.
"""

from datetime import date, datetime
from decimal import Decimal

from app.state import (
    DefendantCard,
    EventCard,
    LawyerRequisites,
    ServiceRow,
    ExtraDecreeRow,
)


# ─── Вспомогательные преобразования ─────────────────────────────────────

def _date_to_str(value):
    return value.isoformat() if value else None


def _str_to_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _dec_to_str(value):
    return str(value if value is not None else Decimal("0.00"))


def _str_to_dec(value):
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0.00")


def _ef_to_dict(ef):
    return {"db": ef.db_value, "user": ef.user_value}


def _ef_apply(ef, data, overlay):
    """overlay=True: не трогаем db_value (оставляем свежее из БД)."""
    data = data or {}
    if not overlay:
        ef.set_db_value(data.get("db") or "")
    ef.set_user_value(data.get("user") or "")


# ─── Сериализация ────────────────────────────────────────────────────────

def state_to_dict(state):
    return {
        "version": 1,

        "case_source": state.case_source,
        "petition_or_representation": state.petition_or_representation,

        "fields": {
            "case_number": _ef_to_dict(state.case_number),
            "judicial_uid": _ef_to_dict(state.judicial_uid),
            "decree_date": _ef_to_dict(state.decree_date),
            "judge": _ef_to_dict(state.judge),
            "secretary": _ef_to_dict(state.secretary),
            "prosecutor": _ef_to_dict(state.prosecutor),
            "verdict_date": _ef_to_dict(state.verdict_date),
            "case_sub_type": _ef_to_dict(state.case_sub_type),
        },

        "defendants": [
            {
                "fio": d.fio,
                "sex": d.sex,
                "native": d.native,
                "birth_date": _date_to_str(d.birth_date),
                "article": d.article,
                "in_custody": bool(d.in_custody),
            }
            for d in state.defendants
        ],
        "selected_defendant_index": state.selected_defendant_index,

        "lawyers": [
            {
                "part_id": l.part_id,
                "fio": l.fio,
                "recipient_name": l.recipient_name,
                "inn": l.inn,
                "kpp": l.kpp,
                "account": l.account,
                "bank": l.bank,
                "bik": l.bik,
                "corr_account": l.corr_account,
            }
            for l in state.lawyers
        ],
        "selected_lawyer_index": state.selected_lawyer_index,
        "lawyer_claimed_amount": _dec_to_str(state.lawyer_claimed_amount),

        "events": [
            {
                "event_name": e.event_name,
                "event_result": e.event_result,
                "reason_for_result": e.reason_for_result,
                "event_date": _date_to_str(e.event_date),
            }
            for e in state.events
        ],

        "intro": {
            "use_custom_intro": bool(state.use_custom_intro),
            "intro_mode": state.intro_mode,
            "custom_intro_text": state.custom_intro_text,
            "custom_intro_html": state.custom_intro_html,
            "custom_intro_segments": state.custom_intro_segments or [],
        },

        "payment_rule": {
            "letter": state.payment_rule.letter,
            "add_region_20": bool(state.payment_rule.add_region_20),
            "add_experience_30": bool(state.payment_rule.add_experience_30),
            "grounds": list(state.payment_rule.grounds or []),
        },

        "services": [
            {
                "service_date": _date_to_str(s.service_date),
                "service_name": s.service_name,
                "amount": _dec_to_str(s.amount),
                "is_session": bool(s.is_session),
            }
            for s in state.services
        ],

        "use_extra_decrees": bool(state.use_extra_decrees),
        "extra_decrees": [
            {
                "source": x.source,
                "decree_date": _date_to_str(x.decree_date),
                "amount": _dec_to_str(x.amount),
            }
            for x in state.extra_decrees
        ],

        "prosecutor_proposes_recovery": bool(state.prosecutor_proposes_recovery),
        "defendant_objected": bool(state.defendant_objected),
        "recovery_mode": state.recovery_mode,

        "declension_overrides": dict(state.declension_overrides or {}),
    }


# ─── Восстановление ──────────────────────────────────────────────────────

def apply_dict_to_state(state, data, mode="full"):
    """Применяет снапшот к state.

    mode="full"    — состояние полностью из снапшота (без обращения к БД дел).
    mode="overlay" — состояние уже свежезагружено из БД дел; накладываем
                     пользовательские правки, сохраняя свежие списки.
    """
    overlay = (mode == "overlay")
    data = data or {}

    if not overlay:
        state.case_source = data.get("case_source") or ""
    state.petition_or_representation = (
        data.get("petition_or_representation") or "petition"
    )

    fields = data.get("fields") or {}
    _ef_apply(state.case_number, fields.get("case_number"), overlay)
    _ef_apply(state.judicial_uid, fields.get("judicial_uid"), overlay)
    _ef_apply(state.decree_date, fields.get("decree_date"), overlay)
    _ef_apply(state.judge, fields.get("judge"), overlay)
    _ef_apply(state.secretary, fields.get("secretary"), overlay)
    _ef_apply(state.prosecutor, fields.get("prosecutor"), overlay)
    _ef_apply(state.verdict_date, fields.get("verdict_date"), overlay)
    _ef_apply(state.case_sub_type, fields.get("case_sub_type"), overlay)

    # ── Подсудимые ──
    arch_defendants = data.get("defendants") or []
    if overlay:
        # Свежий список остаётся; накладываем правки по совпадению ФИО
        fresh_by_fio = {d.fio.strip(): d for d in state.defendants}
        for ad in arch_defendants:
            fresh = fresh_by_fio.get((ad.get("fio") or "").strip())
            if fresh is None:
                continue
            fresh.sex = ad.get("sex") or fresh.sex
            fresh.native = ad.get("native") or fresh.native
            fresh.article = ad.get("article") or fresh.article
            fresh.in_custody = bool(ad.get("in_custody"))
            bd = _str_to_date(ad.get("birth_date"))
            if bd:
                fresh.birth_date = bd
        # Выбранный подсудимый — по ФИО
        sel_idx = data.get("selected_defendant_index") or 0
        sel_fio = ""
        if 0 <= sel_idx < len(arch_defendants):
            sel_fio = (arch_defendants[sel_idx].get("fio") or "").strip()
        state.selected_defendant_index = 0
        for i, d in enumerate(state.defendants):
            if d.fio.strip() == sel_fio:
                state.selected_defendant_index = i
                break
    else:
        state.defendants = [
            DefendantCard(
                fio=ad.get("fio") or "",
                sex=ad.get("sex") or "",
                native=ad.get("native") or "",
                birth_date=_str_to_date(ad.get("birth_date")),
                article=ad.get("article") or "",
                in_custody=bool(ad.get("in_custody")),
            )
            for ad in arch_defendants
        ]
        state.selected_defendant_index = data.get("selected_defendant_index") or 0

    # ── Адвокаты ──
    arch_lawyers = data.get("lawyers") or []
    if overlay:
        sel_idx = data.get("selected_lawyer_index") or 0
        sel_fio = ""
        if 0 <= sel_idx < len(arch_lawyers):
            sel_fio = (arch_lawyers[sel_idx].get("fio") or "").strip()

        found_index = None
        for i, l in enumerate(state.lawyers):
            if l.fio.strip() == sel_fio:
                found_index = i
                break

        if found_index is None and sel_fio:
            # Архивного адвоката нет в свежем списке — добавляем его
            al = arch_lawyers[sel_idx]
            state.lawyers.append(LawyerRequisites(
                part_id=al.get("part_id"),
                fio=al.get("fio") or "",
                recipient_name=al.get("recipient_name") or "",
                inn=al.get("inn") or "",
                kpp=al.get("kpp") or "",
                account=al.get("account") or "",
                bank=al.get("bank") or "",
                bik=al.get("bik") or "",
                corr_account=al.get("corr_account") or "",
            ))
            found_index = len(state.lawyers) - 1

        state.selected_lawyer_index = found_index if found_index is not None else 0
    else:
        state.lawyers = [
            LawyerRequisites(
                part_id=al.get("part_id"),
                fio=al.get("fio") or "",
                recipient_name=al.get("recipient_name") or "",
                inn=al.get("inn") or "",
                kpp=al.get("kpp") or "",
                account=al.get("account") or "",
                bank=al.get("bank") or "",
                bik=al.get("bik") or "",
                corr_account=al.get("corr_account") or "",
            )
            for al in arch_lawyers
        ]
        state.selected_lawyer_index = data.get("selected_lawyer_index") or 0

    state.lawyer_claimed_amount = _str_to_dec(data.get("lawyer_claimed_amount"))

    # ── События ── (в overlay-режиме оставляем свежие из БД)
    if not overlay:
        state.events = [
            EventCard(
                event_name=e.get("event_name") or "",
                event_result=e.get("event_result") or "",
                reason_for_result=e.get("reason_for_result") or "",
                event_date=_str_to_date(e.get("event_date")),
            )
            for e in (data.get("events") or [])
        ]

    # ── Вводная часть ──
    intro = data.get("intro") or {}
    state.use_custom_intro = bool(intro.get("use_custom_intro"))
    state.intro_mode = intro.get("intro_mode") or "default"
    state.custom_intro_text = intro.get("custom_intro_text") or ""
    state.custom_intro_html = intro.get("custom_intro_html") or ""
    state.custom_intro_segments = intro.get("custom_intro_segments") or []

    # ── Правило оплаты ──
    pr = data.get("payment_rule") or {}
    state.payment_rule.letter = pr.get("letter") or "G"
    state.payment_rule.add_region_20 = bool(pr.get("add_region_20", True))
    state.payment_rule.add_experience_30 = bool(pr.get("add_experience_30", True))
    state.payment_rule.grounds = list(pr.get("grounds") or [])

    # ── Услуги ──
    state.services = [
        ServiceRow(
            service_date=_str_to_date(s.get("service_date")),
            service_name=s.get("service_name") or "",
            amount=_str_to_dec(s.get("amount")),
            is_session=bool(s.get("is_session")),
        )
        for s in (data.get("services") or [])
    ]

    # ── Дополнительные постановления ──
    state.use_extra_decrees = bool(data.get("use_extra_decrees"))
    state.extra_decrees = [
        ExtraDecreeRow(
            source=x.get("source") or "",
            decree_date=_str_to_date(x.get("decree_date")),
            amount=_str_to_dec(x.get("amount")),
        )
        for x in (data.get("extra_decrees") or [])
    ]

    # ── Радиокнопки ──
    state.prosecutor_proposes_recovery = bool(
        data.get("prosecutor_proposes_recovery", True))
    state.defendant_objected = bool(data.get("defendant_objected", True))
    state.recovery_mode = data.get("recovery_mode") or "recovery"

    state.declension_overrides = dict(data.get("declension_overrides") or {})
