from manim import *
import numpy as np


# ============================================================
# Shared styling
# ============================================================

BG = "#07111F"
WHITE_SOFT = "#F2F4F7"
MUTED = "#8D9AAA"

BLUE = "#6DB8FF"
PURPLE = "#A783FF"
GREEN = "#62D6A7"
AMBER = "#F4C56A"
RED = "#FF7A90"

config.background_color = BG


def title(text):
    return Text(
        text,
        font_size=38,
        color=WHITE_SOFT,
        weight=MEDIUM,
    ).to_edge(UP, buff=0.45)


def subtitle(text):
    return Text(
        text,
        font_size=20,
        color=MUTED,
    )


def qubit(label):
    circle = Circle(
        radius=0.42,
        stroke_width=2.5,
        color=BLUE,
    )

    txt = MathTex(
        label,
        font_size=30,
        color=WHITE_SOFT,
    )

    return VGroup(circle, txt)


def percentage_bar(label, value, color, width=3.7):
    """
    value should be between 0 and 1.
    """

    name = Text(
        label,
        font_size=25,
        color=WHITE_SOFT,
    )

    background = RoundedRectangle(
        width=width,
        height=0.28,
        corner_radius=0.08,
        stroke_width=1,
        stroke_color="#405066",
        fill_color="#172437",
        fill_opacity=1,
    )

    fill_width = max(0.05, width * value)

    fill = RoundedRectangle(
        width=fill_width,
        height=0.28,
        corner_radius=0.08,
        stroke_width=0,
        fill_color=color,
        fill_opacity=1,
    )

    fill.align_to(background, LEFT)

    pct = Text(
        f"{100 * value:.0f}%",
        font_size=23,
        color=WHITE_SOFT,
    )

    row = VGroup(name, background, fill, pct)

    name.next_to(background, LEFT, buff=0.25)
    pct.next_to(background, RIGHT, buff=0.25)

    return row


# ============================================================
# 1. Hamiltonian Drift
# Slide 4
# ============================================================

class HamiltonianDrift(Scene):

    def construct(self):

        header = title("A calibrated interaction drifts")

        equation = MathTex(
            r"H_0",
            r"\longrightarrow",
            r"H_{\mathrm{true}} = H_0 + \delta P_r",
            font_size=37,
        )

        equation[0].set_color(WHITE_SOFT)
        equation[1].set_color(MUTED)
        equation[2].set_color(WHITE_SOFT)

        equation.next_to(header, DOWN, buff=0.45)

        self.play(FadeIn(header))
        self.play(Write(equation))

        # ------------------------
        # Qubit chain
        # ------------------------

        qs = [
            qubit(r"q_0"),
            qubit(r"q_1"),
            qubit(r"q_2"),
            qubit(r"q_3"),
        ]

        qs_group = VGroup(*qs).arrange(RIGHT, buff=1.55)
        qs_group.move_to(DOWN * 0.3)

        coupling_lines = VGroup()
        coupling_labels = VGroup()

        names = [
            r"J_{01}",
            r"J_{12}",
            r"J_{23}",
        ]

        for i in range(3):

            line = Line(
                qs[i].get_right(),
                qs[i + 1].get_left(),
                color=MUTED,
                stroke_width=4,
            )

            label = MathTex(
                names[i],
                r"=1.00",
                font_size=27,
                color=WHITE_SOFT,
            )

            label.next_to(line, UP, buff=0.12)

            coupling_lines.add(line)
            coupling_labels.add(label)

        self.play(
            LaggedStart(
                *[FadeIn(q) for q in qs],
                lag_ratio=0.12,
            )
        )

        self.play(
            LaggedStart(
                *[Create(line) for line in coupling_lines],
                lag_ratio=0.15,
            )
        )

        self.play(FadeIn(coupling_labels))

        self.wait(0.7)

        # ------------------------
        # Highlight J23
        # ------------------------

        target_line = coupling_lines[2]
        target_label = coupling_labels[2]

        self.play(
            target_line.animate.set_color(AMBER),
            target_label.animate.set_color(AMBER),
        )

        delta_label = MathTex(
            r"\delta=-0.35",
            font_size=32,
            color=AMBER,
        )

        delta_label.next_to(target_line, DOWN, buff=0.35)

        self.play(FadeIn(delta_label, shift=UP * 0.1))

        # replace J23 value
        new_label = MathTex(
            r"J_{23}",
            r"=0.65",
            font_size=27,
            color=AMBER,
        )

        new_label.move_to(target_label)

        self.play(
            Transform(target_label, new_label),
        )

        drift_term = MathTex(
            r"H_{\mathrm{true}}",
            r"=",
            r"H_0",
            r"-0.35\,Z_2Z_3",
            font_size=35,
        )

        drift_term[0].set_color(WHITE_SOFT)
        drift_term[1].set_color(MUTED)
        drift_term[2].set_color(WHITE_SOFT)
        drift_term[3].set_color(AMBER)

        drift_term.to_edge(DOWN, buff=0.6)

        self.play(Write(drift_term))

        self.wait(1.5)


# ============================================================
# 2. Bayesian Posterior Update
# Slide 8
#
# Values are schematic / illustrative, not a recorded run.
# ============================================================

class BayesianPosterior(Scene):

    def construct(self):

        header = title("Measurements update the posterior")

        note = Text(
            "schematic example",
            font_size=17,
            color=MUTED,
        ).next_to(header, DOWN, buff=0.08)

        self.play(FadeIn(header), FadeIn(note))

        prior_text = Text(
            "Before measurement",
            font_size=27,
            color=MUTED,
        )

        prior_text.next_to(note, DOWN, buff=0.45)

        self.play(FadeIn(prior_text))

        # ------------------------
        # Initial posterior
        # ------------------------

        bars = VGroup(
            percentage_bar("J01", 1 / 3, BLUE),
            percentage_bar("J12", 1 / 3, PURPLE),
            percentage_bar("J23", 1 / 3, GREEN),
        ).arrange(DOWN, buff=0.42)

        bars.move_to(UP * 0.15)

        self.play(
            LaggedStart(
                *[FadeIn(row, shift=RIGHT * 0.1) for row in bars],
                lag_ratio=0.12,
            )
        )

        self.wait(0.6)

        # ------------------------
        # Measurement card
        # ------------------------

        measurement_box = RoundedRectangle(
            width=5.2,
            height=1.1,
            corner_radius=0.15,
            color="#405066",
            fill_color="#111E2D",
            fill_opacity=1,
        )

        measurement_box.to_edge(DOWN, buff=0.45)

        measure_title = Text(
            "New finite-shot measurement",
            font_size=23,
            color=WHITE_SOFT,
        )

        measure_result = Text(
            "128 shots  →  observed count",
            font_size=20,
            color=AMBER,
        )

        measurement_text = VGroup(
            measure_title,
            measure_result,
        ).arrange(DOWN, buff=0.12)

        measurement_text.move_to(measurement_box)

        self.play(
            FadeIn(measurement_box),
            FadeIn(measurement_text),
        )

        self.wait(0.5)

        bayes = MathTex(
            r"P(h\mid D)",
            r"\propto",
            r"P(D\mid h)",
            r"P(h)",
            font_size=37,
        )

        bayes[0].set_color(GREEN)
        bayes[1].set_color(MUTED)
        bayes[2].set_color(AMBER)
        bayes[3].set_color(BLUE)

        bayes.next_to(measurement_box, UP, buff=0.3)

        self.play(Write(bayes))

        self.wait(0.5)

        # ------------------------
        # Posterior update 1
        # ------------------------

        post1 = VGroup(
            percentage_bar("J01", 0.17, BLUE),
            percentage_bar("J12", 0.21, PURPLE),
            percentage_bar("J23", 0.62, GREEN),
        ).arrange(DOWN, buff=0.42)

        post1.move_to(bars)

        after1 = Text(
            "After update",
            font_size=27,
            color=MUTED,
        )

        after1.move_to(prior_text)

        self.play(
            Transform(prior_text, after1),
            Transform(bars, post1),
        )

        self.wait(0.7)

        # ------------------------
        # Posterior update 2
        # ------------------------

        post2 = VGroup(
            percentage_bar("J01", 0.04, BLUE),
            percentage_bar("J12", 0.05, PURPLE),
            percentage_bar("J23", 0.91, GREEN),
        ).arrange(DOWN, buff=0.42)

        post2.move_to(bars)

        second_data = Text(
            "more evidence",
            font_size=19,
            color=AMBER,
        ).next_to(measurement_box, UP, buff=0.12)

        self.play(
            FadeOut(bayes),
            FadeIn(second_data),
        )

        self.play(
            Transform(bars, post2),
        )

        conclusion = MathTex(
            r"P(J_{23}\mid D)",
            r"\approx",
            r"0.91",
            font_size=38,
        )

        conclusion[0].set_color(GREEN)
        conclusion[1].set_color(MUTED)
        conclusion[2].set_color(GREEN)

        conclusion.to_edge(DOWN, buff=0.58)

        self.play(
            FadeOut(measurement_box),
            FadeOut(measurement_text),
            FadeOut(second_data),
            FadeIn(conclusion),
        )

        self.wait(1.5)


# ============================================================
# 3. Expected Information Gain
# Slide 9
#
# The example probabilities are schematic.
# ============================================================

class ExpectedInformationGain(Scene):

    def construct(self):

        header = title("Which experiment should we run next?")

        note = Text(
            "schematic information-gain example",
            font_size=17,
            color=MUTED,
        ).next_to(header, DOWN, buff=0.08)

        self.play(FadeIn(header), FadeIn(note))

        current = VGroup(
            Text(
                "Current posterior",
                font_size=25,
                color=MUTED,
            ),
            MathTex(
                r"J_{01}:33\%",
                r"\qquad",
                r"J_{12}:33\%",
                r"\qquad",
                r"J_{23}:34\%",
                font_size=30,
            ),
        ).arrange(DOWN, buff=0.15)

        current.next_to(note, DOWN, buff=0.35)

        self.play(FadeIn(current))

        # ------------------------
        # Three experiment cards
        # ------------------------

        cards = VGroup()

        card_specs = [
            (
                "Experiment A",
                ["36%", "30%", "34%"],
                0.06,
            ),
            (
                "Experiment B",
                ["5%", "10%", "85%"],
                0.62,
            ),
            (
                "Experiment C",
                ["27%", "41%", "32%"],
                0.10,
            ),
        ]

        for name, probs, score in card_specs:

            box = RoundedRectangle(
                width=3.55,
                height=2.65,
                corner_radius=0.15,
                stroke_color="#405066",
                fill_color="#101D2B",
                fill_opacity=1,
            )

            card_title = Text(
                name,
                font_size=24,
                color=WHITE_SOFT,
            )

            outcomes = VGroup(
                Text(
                    f"J01   {probs[0]}",
                    font_size=20,
                    color=BLUE,
                ),
                Text(
                    f"J12   {probs[1]}",
                    font_size=20,
                    color=PURPLE,
                ),
                Text(
                    f"J23   {probs[2]}",
                    font_size=20,
                    color=GREEN,
                ),
            ).arrange(DOWN, buff=0.08)

            eig = Text(
                f"expected gain  {score:.2f}",
                font_size=18,
                color=MUTED,
            )

            contents = VGroup(
                card_title,
                outcomes,
                eig,
            ).arrange(DOWN, buff=0.24)

            contents.move_to(box)

            cards.add(VGroup(box, contents))

        cards.arrange(RIGHT, buff=0.35)
        cards.move_to(DOWN * 0.35)

        self.play(
            LaggedStart(
                *[FadeIn(card, shift=UP * 0.1) for card in cards],
                lag_ratio=0.15,
            )
        )

        self.wait(0.8)

        # ------------------------
        # Compare uncertainty
        # ------------------------

        formula = MathTex(
            r"\mathrm{EIG}(e)",
            r"=",
            r"H_{\mathrm{now}}",
            r"-",
            r"\mathbb{E}[H_{\mathrm{after}}]",
            font_size=32,
        )

        formula[0].set_color(AMBER)
        formula[1].set_color(MUTED)
        formula[2].set_color(WHITE_SOFT)
        formula[3].set_color(MUTED)
        formula[4].set_color(WHITE_SOFT)

        formula.to_edge(DOWN, buff=0.45)

        self.play(Write(formula))

        self.wait(0.5)

        # highlight experiment B
        b_box = cards[1][0]

        self.play(
            b_box.animate.set_stroke(
                GREEN,
                width=4,
            ),
            cards[0].animate.set_opacity(0.35),
            cards[2].animate.set_opacity(0.35),
        )

        choice = MathTex(
            r"e^*",
            r"=",
            r"\arg\max_e\,\mathrm{EIG}(e)",
            font_size=38,
        )

        choice[0].set_color(GREEN)
        choice[1].set_color(MUTED)
        choice[2].set_color(GREEN)

        choice.move_to(formula)

        self.play(
            Transform(formula, choice),
        )

        choose_label = Text(
            "choose Experiment B",
            font_size=26,
            color=GREEN,
        ).next_to(cards[1], DOWN, buff=0.2)

        self.play(FadeIn(choose_label))

        self.wait(1.5)


# ============================================================
# 4. LOCALIZE -> CALIBRATE
# Slide 10
#
# Posterior numbers are schematic to illustrate the policy.
# ============================================================

class LocalizeCalibrate(Scene):

    def construct(self):

        header = title("Q-Scope changes objectives as it learns")

        note = Text(
            "schematic policy progression",
            font_size=17,
            color=MUTED,
        ).next_to(header, DOWN, buff=0.08)

        self.play(FadeIn(header), FadeIn(note))

        mode = Text(
            "LOCALIZE",
            font_size=39,
            color=PURPLE,
            weight=BOLD,
        )

        question = Text(
            "Which coupling changed?",
            font_size=24,
            color=MUTED,
        )

        mode_group = VGroup(
            mode,
            question,
        ).arrange(DOWN, buff=0.08)

        mode_group.next_to(note, DOWN, buff=0.3)

        self.play(FadeIn(mode_group))

        # ------------------------
        # Initial posterior
        # ------------------------

        bars = VGroup(
            percentage_bar("J01", 0.33, BLUE),
            percentage_bar("J12", 0.33, PURPLE),
            percentage_bar("J23", 0.34, GREEN),
        ).arrange(DOWN, buff=0.38)

        bars.move_to(DOWN * 0.25)

        self.play(
            LaggedStart(
                *[FadeIn(row) for row in bars],
                lag_ratio=0.12,
            )
        )

        threshold_line = VGroup(
            Text(
                "switch threshold",
                font_size=18,
                color=MUTED,
            ),
            MathTex(
                r"90\%",
                font_size=27,
                color=AMBER,
            ),
        ).arrange(RIGHT, buff=0.15)

        threshold_line.to_edge(DOWN, buff=0.55)

        self.play(FadeIn(threshold_line))

        # ------------------------
        # Posterior becomes concentrated
        # ------------------------

        state2 = VGroup(
            percentage_bar("J01", 0.09, BLUE),
            percentage_bar("J12", 0.13, PURPLE),
            percentage_bar("J23", 0.78, GREEN),
        ).arrange(DOWN, buff=0.38)

        state2.move_to(bars)

        self.play(
            Transform(bars, state2),
        )

        self.wait(0.5)

        state3 = VGroup(
            percentage_bar("J01", 0.03, BLUE),
            percentage_bar("J12", 0.04, PURPLE),
            percentage_bar("J23", 0.93, GREEN),
        ).arrange(DOWN, buff=0.38)

        state3.move_to(bars)

        self.play(
            Transform(bars, state3),
        )

        self.wait(0.6)

        crossed = Text(
            "location confidence > 90%",
            font_size=22,
            color=AMBER,
        )

        crossed.next_to(bars, DOWN, buff=0.35)

        self.play(FadeIn(crossed))

        # ------------------------
        # Switch mode
        # ------------------------

        new_mode = Text(
            "CALIBRATE",
            font_size=39,
            color=GREEN,
            weight=BOLD,
        )

        new_question = Text(
            "How large is the drift?",
            font_size=24,
            color=MUTED,
        )

        new_group = VGroup(
            new_mode,
            new_question,
        ).arrange(DOWN, buff=0.08)

        new_group.move_to(mode_group)

        self.play(
            Transform(mode_group, new_group),
            FadeOut(threshold_line),
            FadeOut(crossed),
            FadeOut(bars),
        )

        # ------------------------
        # Drift posterior
        # ------------------------

        delta_values = [
            -0.45,
            -0.40,
            -0.35,
            -0.30,
            -0.25,
        ]

        weights = [
            0.05,
            0.16,
            0.58,
            0.17,
            0.04,
        ]

        axes = Axes(
            x_range=[-0.48, -0.22, 0.05],
            y_range=[0, 0.65, 0.2],
            x_length=7.0,
            y_length=3.0,
            axis_config={
                "color": "#506176",
                "stroke_width": 2,
            },
            x_axis_config={
                "numbers_to_include": delta_values,
                "font_size": 20,
            },
            y_axis_config={
                "numbers_to_include": [],
            },
            tips=False,
        )

        axes.move_to(DOWN * 0.35)

        bars_delta = VGroup()

        for x, w in zip(delta_values, weights):

            bar = Rectangle(
                width=0.55,
                height=max(0.08, w * 4.0),
                stroke_width=0,
                fill_color=GREEN if x == -0.35 else PURPLE,
                fill_opacity=0.9,
            )

            bar.move_to(
                axes.c2p(x, 0)
                + UP * bar.height / 2
            )

            bars_delta.add(bar)

        delta_label = MathTex(
            r"P(\delta\mid J_{23},D)",
            font_size=31,
            color=WHITE_SOFT,
        ).next_to(axes, LEFT, buff=0.3)

        self.play(
            Create(axes),
            FadeIn(delta_label),
        )

        self.play(
            LaggedStart(
                *[
                    GrowFromEdge(bar, DOWN)
                    for bar in bars_delta
                ],
                lag_ratio=0.10,
            )
        )

        estimate = MathTex(
            r"\hat{\delta}",
            r"\approx",
            r"-0.35",
            font_size=37,
        )

        estimate[0].set_color(GREEN)
        estimate[1].set_color(MUTED)
        estimate[2].set_color(GREEN)

        estimate.to_edge(DOWN, buff=0.45)

        self.play(Write(estimate))

        self.wait(0.7)

        # ------------------------
        # Stopping condition
        # ------------------------

        done_box = RoundedRectangle(
            width=6.3,
            height=1.2,
            corner_radius=0.14,
            stroke_color=GREEN,
            stroke_width=2.5,
            fill_color="#10261F",
            fill_opacity=1,
        )

        done_box.move_to(DOWN * 0.65)

        done_text = VGroup(
            Text(
                "DIAGNOSIS COMPLETE",
                font_size=27,
                color=GREEN,
                weight=BOLD,
            ),
            Text(
                "location ≥ 98%   •   90% CI width ≤ 0.05",
                font_size=20,
                color=WHITE_SOFT,
            ),
        ).arrange(DOWN, buff=0.12)

        done_text.move_to(done_box)

        self.play(
            FadeOut(axes),
            FadeOut(bars_delta),
            FadeOut(delta_label),
            FadeOut(estimate),
        )

        self.play(
            FadeIn(done_box),
            FadeIn(done_text),
        )

        self.wait(1.5)