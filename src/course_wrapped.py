import numpy as np
from manim import (
    BLUE,
    DOWN,
    DR,
    GREEN,
    LEFT,
    ORANGE,
    ORIGIN,
    PI,
    PINK,
    RED,
    UP,
    UR,
    YELLOW,
    Dot,
    FadeIn,
    FadeOut,
    Scene,
    StreamLines,
    Text,
    VGroup,
    Write,
)


class CourseWrapped(Scene):
    def create_background(self):
        """
        Creates a continuous, moving background effect with streamlines.
        """
        func = lambda pos: np.sin(pos[0] / 2) * UR + np.cos(pos[1] / 2) * LEFT
        stream_lines = StreamLines(func, stroke_width=2, max_anchors_per_line=30)
        self.add(stream_lines)
        stream_lines.start_animation(warm_up=False, flow_speed=1.5)
        return stream_lines

    def adjust_text_scale_and_break(self, text, max_width=30):
        """
        Adjusts the scale of the text based on its length and breaks it into multiple lines if necessary.

        Args:
            text (str): The input text to adjust.
            max_width (int): Maximum number of characters per line before breaking.

        Returns:
            Text: A Manim Text object with adjusted scale and line breaks.
        """
        # Break text into multiple lines based on max_width
        lines = []
        while len(text) > max_width:
            break_index = text.rfind(" ", 0, max_width)
            if break_index == -1:
                break_index = max_width
            lines.append(text[:break_index])
            text = text[break_index:].strip()
        lines.append(text)

        # Join lines with \n and adjust scale based on length
        formatted_text = "\n".join(lines)
        scale_factor = max(0.5, min(1.2, 25 / len(formatted_text)))
        return Text(formatted_text, width=10).scale(scale_factor)

    def construct(self) -> None:
        # Create and add continuous background motion
        background = self.create_background()
        self.add(background)

        # 1. Opening Text
        opening_text = self.adjust_text_scale_and_break(
            "We've reached the grand finale!",
            max_width=20,
        ).move_to(ORIGIN)
        self.play(Write(opening_text))
        self.wait(2)
        self.play(FadeOut(opening_text))

        # 2. Semester Highlights
        highlights_text = self.adjust_text_scale_and_break(
            "Take a moment to reflect on our incredible semester",
            max_width=25,
        ).move_to(ORIGIN)
        self.play(Write(highlights_text))
        self.wait(2)
        self.play(FadeOut(highlights_text))

        # 3. Key Terms with Enhanced Randomized "Pop" Effect
        key_terms = [
            "tf-idf",
            "rm3",
            "bm25",
            "df",
            "precision",
            "recall",
            "F1-score",
            "query expansion",
        ]
        displayed_terms = []
        for _, term in enumerate(key_terms):
            term_text = (
                Text(term, width=8).scale(np.random.uniform(0.8, 1.2)).set_color(YELLOW)
            )
            random_position = np.append(
                np.random.uniform(-2, 2, size=2),
                0,
            )  # Center the terms more tightly
            term_text.move_to(random_position)
            term_text.rotate(np.random.uniform(-PI / 4, PI / 4))
            if len(displayed_terms) > 0:
                self.play(
                    FadeOut(displayed_terms.pop(0)),
                    run_time=0.5,
                )  # Fade out the oldest term
            self.play(Write(term_text, run_time=1))
            displayed_terms.append(term_text)
        # Ensure all terms fade out at the end
        for term_text in displayed_terms:
            self.play(FadeOut(term_text), run_time=0.5)

        # 4. Introduction to Winners
        winners_intro = self.adjust_text_scale_and_break(
            "Drumroll, please... it's time for the winners!",
            max_width=30,
        ).move_to(ORIGIN)
        self.play(Write(winners_intro))
        self.wait(2)
        self.play(FadeOut(winners_intro))

        # 5. Build-up Scene
        buildup_text = self.adjust_text_scale_and_break(
            "But first, let's give it up for our Honorable Mentions",
            max_width=30,
        ).move_to(ORIGIN)
        self.play(Write(buildup_text))
        self.wait(2)
        self.play(FadeOut(buildup_text))

        # TODO(Eilon): Change to actual results
        honorable_mentions = ["5th Place: Bob", "4th Place: Alice"]
        for mention in honorable_mentions:
            mention_text = self.adjust_text_scale_and_break(
                mention,
                max_width=30,
            ).move_to(ORIGIN)
            self.play(Write(mention_text))
            self.wait(2)
            self.play(FadeOut(mention_text))

        buildup_winner = self.adjust_text_scale_and_break(
            "Alright, here we go...",
            max_width=30,
        ).move_to(ORIGIN)
        self.play(Write(buildup_winner))
        self.wait(2)
        self.play(FadeOut(buildup_winner))

        # TODO(Eilon): Change to actual results
        winners = ["3rd Place: Eve", "2nd Place: David", "1st Place: Charlie"]
        podium = VGroup()
        confetti = VGroup()

        positions = [DOWN * 3, ORIGIN, UP * 3, ORIGIN]
        for i, winner in enumerate(winners):
            winner_text = self.adjust_text_scale_and_break(winner, max_width=30)
            winner_text.move_to(positions[i])
            self.play(Write(winner_text))
            self.wait(1)
            podium.add(winner_text)

        self.wait(1)
        self.play(FadeIn(podium))

        # Fade out background to enhance confetti effect
        self.play(FadeOut(background))

        # Add confetti cannon effect with specific angles
        cannon_position = DR + DOWN * 0.5
        screen_bounds = [
            -7,
            7,
            -4,
            4,
        ]  # [left, right, bottom, top] bounds of the screen

        for _ in range(8):  # Shoot in random batches
            confetti_batch = VGroup()
            for __ in range(150):  # Batch of 150 particles
                dot = Dot(
                    radius=0.05,
                    color=np.random.choice([RED, GREEN, BLUE, YELLOW, PINK, ORANGE]),
                )
                dot.move_to(cannon_position)
                angle = np.random.uniform(
                    0,
                    2 * PI,
                )  # Randomize direction across the screen
                distance = np.random.uniform(3, 7)
                target_x = distance * np.cos(angle)
                target_y = distance * np.sin(angle)

                # Clamp confetti positions to screen bounds
                target_x = max(screen_bounds[0], min(target_x, screen_bounds[1]))
                target_y = max(screen_bounds[2], min(target_y, screen_bounds[3]))

                target_position = np.array([target_x, target_y, 0])
                dot.shift(target_position / 3)  # Adjust spread
                confetti_batch.add(dot)

            self.play(
                confetti_batch.animate.shift(target_position),
                run_time=1.5,
                lag_ratio=0.05,
            )
            self.play(FadeOut(confetti_batch), run_time=0.5)

        self.wait(5)
        self.play(FadeOut(podium), FadeOut(confetti))


# To render and check it looks ok, save this script and run:
# manim -pql course_wrapped.py CourseWrapped
# To hd render
# manim -pqh course_wrapped.py CourseWrapped
