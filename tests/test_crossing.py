import unittest

from relayloom.ap.crossing import count_crossings


def walk(start, end, frames=10, y=0.5, first=0):
    return [(first + i, start + (end - start) * i / (frames - 1), y) for i in range(frames)]


class CrossingTests(unittest.TestCase):
    def test_each_item_is_counted_once_when_it_crosses(self):
        tracks = {1: walk(0.1, 0.9), 2: walk(0.2, 0.8, first=3), 3: walk(0.0, 0.3)}  # item 3 never reaches the line
        found = count_crossings(tracks, 0.5)
        self.assertEqual((found["count"], found["ids"]), (2, [1, 2]))

    def test_an_item_jittering_on_the_line_is_not_counted(self):
        jitter = [(i, 0.5 + (0.01 if i % 2 else -0.01), 0.5) for i in range(12)]
        self.assertEqual(count_crossings({1: jitter}, 0.5, margin=0.03)["count"], 0)

    def test_an_item_that_crosses_back_and_forth_is_counted_once(self):
        there_and_back = walk(0.1, 0.9) + walk(0.9, 0.1, first=10)
        self.assertEqual(count_crossings({7: there_and_back}, 0.5)["count"], 1)

    def test_direction_matters(self):
        tracks = {1: walk(0.1, 0.9), 2: walk(0.9, 0.1)}
        self.assertEqual(count_crossings(tracks, 0.5, direction="increasing")["ids"], [1])
        self.assertEqual(count_crossings(tracks, 0.5, direction="decreasing")["ids"], [2])
        self.assertEqual(count_crossings(tracks, 0.5, direction="either")["count"], 2)

    def test_a_vertical_axis_and_a_lost_then_found_item(self):
        gap = [(0, 0.5, 0.1), (1, 0.5, 0.2), (30, 0.5, 0.8), (31, 0.5, 0.9)]  # the id returns after a gap
        self.assertEqual(count_crossings({5: gap}, 0.5, axis="y")["count"], 1)


if __name__ == "__main__":
    unittest.main()
