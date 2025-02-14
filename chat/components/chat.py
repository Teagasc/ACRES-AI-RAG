import reflex as rx
import reflex_chakra as rc

from chat.components import loading_icon
from chat.state import QA, State

message_style = dict(display="inline-block", padding="0.7em", border_radius="15px", max_width=["30em", "30em", "50em", "50em", "50em", "50em"])


def message(qa: QA) -> rx.Component:
    """A single question/answer message.

    Args:
        qa: The question/answer pair.

    Returns:
        A component displaying the question/answer pair.
    """
    return rx.box(
        rx.box(
            rx.markdown(
                qa.question,
                background_color=rx.color("mauve", 4),
                color=rx.color("mauve", 12),
                **message_style,
            ),
            text_align="right",
            margin_top="1em",
        ),
        rx.box(
            rx.markdown(
                qa.answer,
                background_color=rx.color("mauve", 1),
                color=rx.color("accent", 12),
                **message_style,
            ),
            text_align="left",
            padding_top="1em",
        ),

        rx.cond(
            qa.show_sources,
            rx.accordion.root(
                rx.accordion.item(
                    header="Sources",
                    content=rx.foreach
                        (qa.sources,
                         lambda src: rx.link(
                             src,
                             href=src,
                             target="_blank",
                             display="block"
                            )
                         ),
                ),

            collapsible=True,
            type="multiple",
            variant="outline",
            margin_top="0.2em",
            display="inline-block",
            max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
            border_radius="15px",
    )


        # rx.cond(
        #     qa.show_sources,
        #     rx.box(
        #         rx.text("Sources:", font_weight="bold", margin_bottom="0.5em"),
        #         rx.box(
        #             rx.foreach(qa.sources, lambda src: rx.link(src, href=src, target="_blank")),
        #             display="flex",
        #             flex_direction="column",
        #             gap="0.5em",
        #         ),
        #         background_color=rx.color("sage", 6),
        #         **message_style,
        #     )
        ),
        width="100%",
    )


def chat() -> rx.Component:
    """List all the messages in a single conversation."""
    return rx.vstack(
        rx.box(rx.foreach(State.chats[State.current_chat], message), width="100%"),
        py="8",
        flex="1",
        width="100%",
        max_width="50em",
        padding_x="4px",
        align_self="center",
        overflow="hidden",
        padding_bottom="5em",
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.center(
        rx.vstack(
            rc.form(
                rc.form_control(
                    rx.hstack(
                        rx.input(
                            rx.input.slot(

                            ),
                            placeholder="Ask anything...",
                            id="question",
                            width=["15em", "20em", "45em", "50em", "50em", "50em"],
                            height=["1em", "1em", "2em", "4em", "4em", "4em"],
                            border_radius="15px",
                            font_size="1em",
                        ),
                        rx.button(
                            rx.cond(
                                State.processing,
                                loading_icon(height="2em"),
                                rx.icon("arrow-up", height="2.25em", width="2.25em"),
                            ),
                            type="submit",
                            height="4em",
                            width="4em",
                            border_radius="50px",
                            padding="0",
                            margin="0",
                        ),
                        align_items="center",
                    ),
                    is_disabled=State.processing,
                ),
                on_submit=State.process_question,
                reset_on_submit=True,
            ),
            rx.text(
                "ACRES Assistant may return factually incorrect or misleading responses. Use discretion.",
                text_align="center",
                font_size="0.75em",
                color=rx.color("mauve", 10),
            ),
            margin_top="0.25em",
            margin_bottom="0.75em",
            align_items="center",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="8px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align_items="stretch",
        width="100%",
        style={"zIndex": "9999"},
    )
