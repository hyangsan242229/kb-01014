import html
import random
import time
from pathlib import Path

import streamlit as st

MOLE_DURATION_SECONDS = 1.5
image_dir = Path(__file__).parent


def initialize_game_state():
    defaults = {
        'mole_position': random.randrange(9),
        'score': 0,
        'lives': 3,
        'mole_number': 1,
        'mole_spawned_at': time.monotonic(),
        'resolved_mole_number': 0,
        'game_over': False,
        'game_message': '',
    }
    for name, value in defaults.items():
        if name not in st.session_state:
            st.session_state[name] = value


def show_next_mole():
    previous_position = st.session_state.mole_position
    next_positions = [hole for hole in range(9) if hole != previous_position]
    st.session_state.mole_number += 1
    st.session_state.mole_position = random.choice(next_positions)
    st.session_state.mole_spawned_at = time.monotonic()


def handle_missed_mole(mole_number):
    if (
        st.session_state.game_over
        or mole_number != st.session_state.mole_number
        or mole_number == st.session_state.resolved_mole_number
    ):
        return

    st.session_state.resolved_mole_number = mole_number
    st.session_state.lives = max(0, st.session_state.lives - 1)
    if st.session_state.lives == 0:
        st.session_state.game_over = True
        st.session_state.game_message = ''
        return

    st.session_state.game_message = '시간이 끝났어요! 라이프가 1 줄었습니다.'
    show_next_mole()


def handle_hole_click(position, mole_number):
    if (
        st.session_state.game_over
        or mole_number != st.session_state.mole_number
        or mole_number == st.session_state.resolved_mole_number
    ):
        return

    if position != st.session_state.mole_position:
        st.session_state.game_message = ''
        return

    elapsed = time.monotonic() - st.session_state.mole_spawned_at
    if elapsed >= MOLE_DURATION_SECONDS:
        handle_missed_mole(mole_number)
        return

    st.session_state.resolved_mole_number = mole_number
    st.session_state.score += 10
    st.session_state.game_message = '두더지를 잡았습니다!'
    show_next_mole()


def update_elapsed_time_and_misses():
    mole_number = st.session_state.mole_number
    elapsed = time.monotonic() - st.session_state.mole_spawned_at
    if (
        not st.session_state.game_over
        and mole_number != st.session_state.resolved_mole_number
        and elapsed >= MOLE_DURATION_SECONDS
    ):
        handle_missed_mole(mole_number)


@st.cache_data
def load_image(image_path):
    return Path(image_path).read_bytes()


def render_game():
    update_elapsed_time_and_misses()

    shown_mole_number = st.session_state.mole_number
    score_column, lives_column, time_column = st.columns(3)
    score_display = score_column.empty()
    lives_display = lives_column.empty()
    time_display = time_column.empty()
    elapsed_display = time_column.empty()

    columns = st.columns(3)
    image_slots = [None] * 9
    game_over_for_buttons = st.session_state.game_over

    for position in range(9):
        with columns[position % 3]:
            image_slots[position] = st.empty()
            clicked = st.button(
                '구멍 클릭',
                key=f'hole_{shown_mole_number}_{position}',
                use_container_width=True,
                disabled=game_over_for_buttons,
            )
            if clicked:
                handle_hole_click(position, shown_mole_number)

    for position, image_slot in enumerate(image_slots):
        mole_is_visible = (
            not st.session_state.game_over
            and position == st.session_state.mole_position
        )
        image_name = 'img.png' if mole_is_visible else 'hole.png'
        image_slot.image(load_image(str(image_dir / image_name)), width=120)

    elapsed_seconds = min(
        max(time.monotonic() - st.session_state.mole_spawned_at, 0),
        MOLE_DURATION_SECONDS,
    )
    remaining_seconds = max(0, MOLE_DURATION_SECONDS - elapsed_seconds)
    score_display.metric('현재 점수', f"{st.session_state.score}점")
    lives_display.metric('라이프', st.session_state.lives)
    time_display.metric('남은 시간', f'{remaining_seconds:.1f}초')
    elapsed_display.caption(f'경과 시간: {elapsed_seconds:.1f}초')

    if st.session_state.game_over:
        message = f"게임 오버! 최종 점수: {st.session_state.score}점"
        message_color = '#b00020'
    else:
        message = st.session_state.game_message
        message_color = '#2e7d32'
    st.markdown(
        '<div style="min-height: 2rem; display: flex; align-items: center; '
        f'color: {message_color}; font-weight: 600;">'
        f'{html.escape(message) or "&nbsp;"}</div>',
        unsafe_allow_html=True,
    )


st.set_page_config(page_title='두더지 잡기 게임', page_icon='🐹')
initialize_game_state()
st.title('두더지 잡기 게임')
st.write('두더지를 클릭해 보세요!')


@st.fragment(run_every=0.1)
def game_fragment():
    render_game()


game_fragment()