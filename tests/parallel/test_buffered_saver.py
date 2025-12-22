from unittest.mock import Mock

import pytest

from pysatl_experiment.parallel.buffered_saver import BufferedSaver


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
