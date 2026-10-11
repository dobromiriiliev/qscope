from manim import *

config.background_color = "#08111B"

TITLE = WHITE
TEXT = "#DCE7F5"
MUTED = "#90A7C0"

CYAN = "#5CCBFF"
GREEN = "#66DBA5"
VIOLET = "#A38CFF"
AMBER = "#FFC166"
PINK = "#FF7F97"

PANEL = "#0F1A28"
BORDER = "#20364F"
TRACK = "#172638"


def make_panel(width, height):
    return RoundedRectangle(
        corner_radius=0.18,
        width=width,
        height=height,
        stroke_color=BORDER,
        stroke_width=2,
        fill_color=PANEL,
        fill_opacity=1,
    )


def small_bar(label, value_text, frac, color, width=2.0):
    label_t = Text(label, font_size=18, color=TEXT, weight=BOLD)
    value_t = Text(value_text, font_size=18, color=WHITE)

    track = RoundedRectangle(
        corner_radius=0.07,
        width=width,
        height=0.18,
        stroke_width=0,
        fill_color=TRACK,
        fill_opacity=1,
    )

    fill = RoundedRectangle(
        corner_radius=0.07,
        width=max(0.01, width * max(0, min(1, frac))),
        height=0.18,
        stroke_width=0,
        fill_color=color,
        fill_opacity=1,
    )
    fill.align_to(track, LEFT)
    fill.move_to(track.get_left() + RIGHT * (fill.width / 2))

    row = VGroup(label_t, VGroup(track, fill), value_t).arrange(RIGHT, buff=0.16)
    return row


class QScopeThumbnailFinal(Scene):
    def construct(self):
        # ----- Header -----
        title = Text("Q-Scope", font_size=46, color=TITLE, weight=BOLD)
        subtitle = Text(
            "Adaptive Hamiltonian Drift Diagnosis with Qiskit",
            font_size=20,
            color=CYAN,
        )
        title.to_edge(UP, buff=0.22)
        subtitle.next_to(title, DOWN, buff=0.06)

        rule = Line(
            LEFT * 6.7,
            RIGHT * 6.7,
            stroke_color="#17304B",
            stroke_width=2,
        ).next_to(subtitle, DOWN, buff=0.18)

        self.add(title, subtitle, rule)

        # ----- Panels -----
        left = make_panel(4.7, 3.45).move_to(LEFT * 3.55 + DOWN * 0.12)
        right = make_panel(4.7, 3.45).move_to(RIGHT * 3.55 + DOWN * 0.12)
        bottom = make_panel(10.2, 1.68).move_to(DOWN * 2.44)

        self.add(left, right, bottom)

        # ===== Left panel: Physical system =====
        left_title = Text("1. Physical system", font_size=26, color=TITLE, weight=BOLD)
        left_title.move_to(left.get_top() + DOWN * 0.34)

        left_sub = Text("4-qubit transverse-field Ising model", font_size=16, color=MUTED)
        left_sub.next_to(left_title, DOWN, buff=0.06)

        xs = [-1.2, -0.4, 0.4, 1.2]
        qubit_center_y = 0.08
        qubits = VGroup()
        fields = VGroup()
        links = VGroup()

        for i, x in enumerate(xs):
            center = left.get_center() + np.array([x, qubit_center_y, 0])

            c = Circle(
                radius=0.22,
                stroke_color=CYAN,
                stroke_width=2.4,
                fill_color="#16273A",
                fill_opacity=1,
            ).move_to(center)
            lbl = Text(f"q{i}", font_size=18, color=WHITE, weight=BOLD).move_to(center)
            qubits.add(VGroup(c, lbl))

            arr = Arrow(
                start=c.get_top() + UP * 0.35,
                end=c.get_top() + UP * 0.05,
                buff=0,
                stroke_width=1.8,
                color=VIOLET,
                max_tip_length_to_length_ratio=0.18,
            )
            arr_lab = Text("X", font_size=15, color=VIOLET, weight=BOLD).next_to(arr, UP, buff=0.01)
            fields.add(VGroup(arr, arr_lab))

        for i, name in enumerate(["J01", "J12", "J23"]):
            line = Line(
                qubits[i][0].get_right(),
                qubits[i + 1][0].get_left(),
                stroke_width=3,
                color=GREEN,
            )
            name_t = Text(name, font_size=15, color=GREEN, weight=BOLD).next_to(line, DOWN, buff=0.07)
            links.add(VGroup(line, name_t))

        fault_box = RoundedRectangle(
            corner_radius=0.14,
            width=3.45,
            height=0.92,
            stroke_color=AMBER,
            stroke_width=2,
            fill_color="#111A27",
            fill_opacity=1,
        ).move_to(left.get_bottom() + UP * 0.66)

        fault_title = Text("Hidden fault", font_size=18, color=AMBER, weight=BOLD)
        fault_l1 = Text("J23 : 1.00 → 0.65", font_size=17, color=WHITE)
        fault_l2 = Text("δ = -0.35", font_size=20, color=PINK, weight=BOLD)
        fault_group = VGroup(fault_title, fault_l1, fault_l2).arrange(DOWN, buff=0.03)
        fault_group.move_to(fault_box.get_center())

        self.add(left_title, left_sub, qubits, fields, links, fault_box, fault_group)

        # ===== Right panel: Adaptive method =====
        right_title = Text("2. Adaptive method", font_size=26, color=TITLE, weight=BOLD)
        right_title.move_to(right.get_top() + DOWN * 0.34)

        right_sub = Text("Choose the next measurement from the posterior", font_size=15, color=MUTED)
        right_sub.next_to(right_title, DOWN, buff=0.06)

        local_box = RoundedRectangle(
            corner_radius=0.14,
            width=1.75,
            height=0.56,
            stroke_color=GREEN,
            stroke_width=2,
            fill_color="#11231E",
            fill_opacity=1,
        )
        cal_box = RoundedRectangle(
            corner_radius=0.14,
            width=1.95,
            height=0.56,
            stroke_color=VIOLET,
            stroke_width=2,
            fill_color="#151F31",
            fill_opacity=1,
        )

        local_lab = Text("LOCALIZE", font_size=21, color=WHITE, weight=BOLD).move_to(local_box.get_center())
        cal_lab = Text("CALIBRATE", font_size=21, color=WHITE, weight=BOLD).move_to(cal_box.get_center())

        stages = VGroup(VGroup(local_box, local_lab), VGroup(cal_box, cal_lab)).arrange(RIGHT, buff=0.26)
        stages.move_to(right.get_center() + UP * 0.77)

        stage_arrow = Arrow(
            stages[0].get_right() + RIGHT * 0.05,
            stages[1].get_left() + LEFT * 0.05,
            buff=0,
            stroke_width=2,
            color=TEXT,
            max_tip_length_to_length_ratio=0.18,
        )

        step1 = RoundedRectangle(
            corner_radius=0.12,
            width=2.5,
            height=0.42,
            stroke_color=GREEN,
            stroke_width=1.8,
            fill_color="#11231E",
            fill_opacity=1,
        )
        step2 = RoundedRectangle(
            corner_radius=0.12,
            width=2.5,
            height=0.42,
            stroke_color=VIOLET,
            stroke_width=1.8,
            fill_color="#151F31",
            fill_opacity=1,
        )
        step3 = RoundedRectangle(
            corner_radius=0.12,
            width=2.5,
            height=0.42,
            stroke_color=CYAN,
            stroke_width=1.8,
            fill_color="#112033",
            fill_opacity=1,
        )
        step4 = RoundedRectangle(
            corner_radius=0.12,
            width=2.5,
            height=0.42,
            stroke_color=WHITE,
            stroke_width=1.6,
            fill_color="#121C2A",
            fill_opacity=1,
        )

        s1 = Text("60 hypotheses", font_size=18, color=GREEN, weight=BOLD).move_to(step1.get_center())
        s2 = Text("98 experiments", font_size=18, color=VIOLET, weight=BOLD).move_to(step2.get_center())
        s3 = Text("128 shots", font_size=18, color=CYAN, weight=BOLD).move_to(step3.get_center())
        s4 = Text("Bayesian update", font_size=18, color=WHITE, weight=BOLD).move_to(step4.get_center())

        step_group = VGroup(
            VGroup(step1, s1),
            VGroup(step2, s2),
            VGroup(step3, s3),
            VGroup(step4, s4),
        ).arrange(DOWN, buff=0.12)
        step_group.move_to(right.get_center() + DOWN * 0.42)

        connectors = VGroup()
        for i in range(len(step_group) - 1):
            connectors.add(
                Arrow(
                    step_group[i].get_bottom() + DOWN * 0.02,
                    step_group[i + 1].get_top() + UP * 0.02,
                    buff=0,
                    stroke_width=1.8,
                    color=MUTED,
                    max_tip_length_to_length_ratio=0.18,
                )
            )

        self.add(right_title, right_sub, stages, stage_arrow, step_group, connectors)

        # ===== Bottom panel: Outcome =====
        bottom_title = Text("3. Outcome", font_size=24, color=TITLE, weight=BOLD)
        bottom_title.move_to(bottom.get_top() + DOWN * 0.24)

        divider = Line(
            bottom.get_center() + UP * 0.42,
            bottom.get_center() + DOWN * 0.42,
            stroke_color="#17304B",
            stroke_width=1.5,
        )

        # Left side: workflow
        workflow_title = Text("Simple workflow", font_size=18, color=MUTED)
        workflow_title.move_to(bottom.get_left() + RIGHT * 1.8 + UP * 0.12)

        w1 = Text("model", font_size=20, color=CYAN, weight=BOLD)
        w2 = Text("measure", font_size=20, color=GREEN, weight=BOLD)
        w3 = Text("update", font_size=20, color=VIOLET, weight=BOLD)
        w4 = Text("diagnose", font_size=20, color=PINK, weight=BOLD)
        workflow = VGroup(w1, w2, w3, w4).arrange(RIGHT, buff=0.18)
        workflow.move_to(bottom.get_left() + RIGHT * 2.1 + DOWN * 0.28)

        workflow_arrows = VGroup()
        for i in range(len(workflow) - 1):
            workflow_arrows.add(
                Arrow(
                    workflow[i].get_right() + RIGHT * 0.02,
                    workflow[i + 1].get_left() + LEFT * 0.02,
                    buff=0,
                    stroke_width=1.7,
                    color=TEXT,
                    max_tip_length_to_length_ratio=0.20,
                )
            )

        # Right side: results only
        results_title = Text("Validation results", font_size=18, color=MUTED)
        results_title.move_to(bottom.get_center() + RIGHT * 2.35 + UP * 0.12)

        row1 = small_bar("Q-Scope", "100%", 1.00, GREEN, width=2.0)
        row2 = small_bar("Fixed", "17%", 0.17, VIOLET, width=2.0)
        row3 = small_bar("Random", "0%", 0.0, "#516170", width=2.0)
        rows = VGroup(row1, row2, row3).arrange(DOWN, buff=0.14, aligned_edge=LEFT)
        rows.move_to(bottom.get_center() + RIGHT * 2.35 + DOWN * 0.27)

        self.add(bottom_title, divider, workflow_title, workflow, workflow_arrows, results_title, rows)

        # Footer
        footer = Text(
            "learn what changed by learning what to measure next",
            font_size=16,
            color=CYAN,
            slant=ITALIC,
        )
        footer.to_edge(DOWN, buff=0.08)

        self.add(footer)
