"""Tests for buffered saver in parallel execution."""

from unittest.mock import Mock

import pytest

from pysatl_experiment.experiment_execution.parallel import BufferedSaver


class TestBufferedSaver:
    def test_exact_buffer_size_flush(self):
        mock_save = Mock()
        saver = BufferedSaver(save_func=mock_save, buffer_size=3)

        for i in range(3):
            saver.add(i)

        assert mock_save.call_count == 1
        assert mock_save.call_args[0][0] == [0, 1, 2]

    def test_partial_flush_at_end(self):
        mock_save = Mock()
        saver = BufferedSaver(save_func=mock_save, buffer_size=5)

        for i in range(3):
            saver.add(i)

        saver.flush()
        assert mock_save.call_count == 1
        assert mock_save.call_args[0][0] == [0, 1, 2]

    def test_empty_flush_is_safe(self):
        mock_save = Mock()
        saver = BufferedSaver(save_func=mock_save, buffer_size=10)
        saver.flush()
        mock_save.assert_not_called()

    def test_save_func_exception_handling(self):
        def failing_save(batch):
            raise RuntimeError("DB connection lost")

        saver = BufferedSaver(save_func=failing_save, buffer_size=2)
        saver.add("item1")

        with pytest.raises(RuntimeError, match="DB connection lost"):
            saver.add("item2")

    @pytest.mark.parametrize("buffer_size", [1, 2, 10, 100])
    def test_buffer_size_edge_cases(self, buffer_size):
        items = list(range(buffer_size * 2 + 1))
        saved_batches = []

        def save_func(batch):
            saved_batches.append(batch)

        saver = BufferedSaver(save_func=save_func, buffer_size=buffer_size)
        for item in items:
            saver.add(item)
        saver.flush()

        flattened = [item for batch in saved_batches for item in batch]
        assert flattened == items

        assert all(len(batch) <= buffer_size for batch in saved_batches[:-1])
        assert len(saved_batches[-1]) <= buffer_size

    # Checks that a buffer size below one is rejected at construction time.
    @pytest.mark.parametrize("buffer_size", [0, -1, -100])
    def test_invalid_buffer_size_is_rejected(self, buffer_size):
        with pytest.raises(ValueError, match="Size of buffer must be at least 1."):
            BufferedSaver(save_func=Mock(), buffer_size=buffer_size)

    # Checks that a rejected construction leaves no saver instance behind.
    def test_invalid_buffer_size_does_not_call_save_func(self):
        with pytest.raises(ValueError, match="Size of buffer must be at least 1."):
            BufferedSaver(save_func=Mock(), buffer_size=0)

    # Checks that the constructor keeps the default buffer size of ten.
    def test_default_buffer_size_is_ten(self):
        saver = BufferedSaver(save_func=Mock())

        assert saver.buffer_size == 10
        assert saver.buffer == []

    # Checks that a single item flushes immediately when the buffer size is one.
    def test_buffer_size_one_flushes_on_every_add(self):
        mock_save = Mock()
        saver = BufferedSaver(save_func=mock_save, buffer_size=1)

        saver.add("a")
        saver.add("b")

        assert mock_save.call_count == 2
        assert [call[0][0] for call in mock_save.call_args_list] == [["a"], ["b"]]

    # Checks that the flush hands over a copy that later mutation cannot alter.
    def test_flush_passes_a_defensive_copy(self):
        captured = []
        saver = BufferedSaver(save_func=captured.append, buffer_size=3)

        saver.add(1)
        saver.add(2)
        saver.add(3)

        captured[0].append(99)

        assert saver.buffer == []
