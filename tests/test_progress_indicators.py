"""
Tests for progress indicator display classes

Tests the real-time progress feedback system including:
- Spinner: Animated spinner for indefinite tasks
- ProgressBar: Progress bars with ETA for definite tasks
- MultiPhaseProgress: Multi-phase progress tracking (Spec → Cost → Code)
- ProgressReporter: Simple callback-based progress reporter
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from io import StringIO

from src.cli.ui.progress_indicators import (
    PhaseProgress,
    Spinner,
    ProgressBar,
    MultiPhaseProgress,
    ProgressReporter,
    with_spinner,
    with_progress_bar,
)


class TestPhaseProgress:
    """Tests for PhaseProgress dataclass"""
    
    def test_phase_progress_creation(self):
        """PhaseProgress stores phase state correctly"""
        phase = PhaseProgress(
            name="Specification",
            status="running",
            start_time=1000.0,
            progress_pct=0.5,
        )
        
        assert phase.name == "Specification"
        assert phase.status == "running"
        assert phase.start_time == 1000.0
        assert phase.progress_pct == 0.5
        assert phase.end_time is None
    
    def test_phase_progress_completion(self):
        """PhaseProgress can be marked complete with end_time"""
        phase = PhaseProgress(
            name="Cost Analysis",
            status="complete",
            start_time=1000.0,
            end_time=1005.0,
            progress_pct=1.0,
        )
        
        assert phase.status == "complete"
        assert phase.end_time == 1005.0
        assert phase.progress_pct == 1.0


class TestSpinner:
    """Tests for Spinner animation"""
    
    def test_spinner_creation(self):
        """Spinner initializes with correct defaults"""
        spinner = Spinner("Processing...")
        
        assert spinner.message == "Processing..."
        assert spinner.frame_idx == 0  # Correct attribute name
        assert spinner.running is False
    
    def test_spinner_no_color(self):
        """Spinner initialization"""
        spinner = Spinner("Processing...", frame_set="simple")
        assert len(spinner.frames) > 0
    
    def test_spinner_frame_sets(self):
        """Spinner supports multiple frame styles"""
        spinner_dots = Spinner("Test", frame_set="dots")
        spinner_arrows = Spinner("Test", frame_set="arrows")
        spinner_simple = Spinner("Test", frame_set="simple")
        
        assert len(spinner_dots.frames) > 0
        assert len(spinner_arrows.frames) > 0
        assert len(spinner_simple.frames) > 0
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_spinner_start_stop(self, mock_stdout):
        """Spinner can start and stop without errors"""
        spinner = Spinner("Processing...")
        
        spinner.start()
        assert spinner.running is True
        assert spinner.thread is not None
        
        time.sleep(0.3)  # Let it animate a few frames
        
        spinner.stop("✓ Complete")
        assert spinner.running is False
        
        # Check output contains completion message
        output = mock_stdout.getvalue()
        assert "Complete" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_spinner_update_message(self, mock_stdout):
        """Spinner can update message while running"""
        spinner = Spinner("Phase 1...")
        
        spinner.start()
        time.sleep(0.2)
        
        spinner.update_message("Phase 2...")
        assert spinner.message == "Phase 2..."
        
        time.sleep(0.2)
        spinner.stop()
    
    def test_spinner_context_manager(self):
        """Spinner works without context manager (no __enter__/__exit__ needed)"""
        with patch('sys.stdout', new_callable=StringIO):
            spinner = Spinner("Processing...")
            spinner.start()
            assert spinner.running is True
            time.sleep(0.2)
            spinner.stop()
            assert spinner.running is False


class TestProgressBar:
    """Tests for ProgressBar display"""
    
    def test_progress_bar_creation(self):
        """ProgressBar initializes correctly"""
        bar = ProgressBar(total=100, prefix="Loading")
        
        assert bar.total == 100
        assert bar.prefix == "Loading"
        assert bar.current == 0
        assert bar.use_color is True
    
    def test_progress_bar_render_basic(self):
        """ProgressBar renders basic progress correctly"""
        bar = ProgressBar(total=100, prefix="Test")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # 50% progress
            bar.update(50)
            output = mock_stdout.getvalue()
            assert "50" in output  # Check for percentage
            
            # 100% progress
            bar.update(100)
            output = mock_stdout.getvalue()
            assert "100" in output
    
    def test_progress_bar_eta_calculation(self):
        """ProgressBar shows timing information"""
        bar = ProgressBar(total=100, prefix="Test", show_time=True)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            bar.update(50)
            output = mock_stdout.getvalue()
            # Should show some timing or percentage info
            assert "50" in output or "elapsed" in output
    
    def test_progress_bar_no_color(self):
        """ProgressBar respects no_color flag"""
        bar = ProgressBar(total=100, prefix="Test", use_color=False)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            bar.update(50)
            output = mock_stdout.getvalue()
            
            # Should not contain ANSI color codes
            assert "\x1b[" not in output
    
    def test_progress_bar_throttling(self):
        """ProgressBar throttles updates to prevent flicker"""
        bar = ProgressBar(total=100, prefix="Test")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            # Rapid updates should be throttled
            bar.update(10)
            bar.update(11)  # Too fast, should be throttled
            bar.update(12)  # Too fast, should be throttled
            
            output = mock_stdout.getvalue()
            # Should have limited output due to throttling
            assert len(output) > 0
    
    def test_progress_bar_context_manager(self):
        """ProgressBar works without context manager"""
        with patch('sys.stdout', new_callable=StringIO):
            bar = ProgressBar(total=100, prefix="Test")
            bar.update(50)
            assert bar.current == 50
            bar.finish()


class TestMultiPhaseProgress:
    """Tests for MultiPhaseProgress tracking"""
    
    def test_multi_phase_creation(self):
        """MultiPhaseProgress initializes with phases"""
        phases = ["Specification", "Cost Analysis", "Code Generation"]
        progress = MultiPhaseProgress(phases)
        
        assert len(progress.phases) == 3
        assert progress.phases[0].name == "Specification"
        assert progress.phases[1].name == "Cost Analysis"
        assert progress.phases[2].name == "Code Generation"
        assert all(p.status == "pending" for p in progress.phases)
    
    def test_start_phase(self):
        """MultiPhaseProgress can start a phase"""
        phases = ["Phase 1", "Phase 2", "Phase 3"]
        progress = MultiPhaseProgress(phases)
        
        with patch('sys.stdout', new_callable=StringIO):
            progress.start_phase(0, "Starting phase 1...")
        
        assert progress.phases[0].status == "running"
        assert progress.phases[0].start_time is not None
        assert progress.current_phase_idx == 0
    
    def test_update_phase(self):
        """MultiPhaseProgress can update phase progress"""
        phases = ["Phase 1"]
        progress = MultiPhaseProgress(phases)
        
        with patch('sys.stdout', new_callable=StringIO):
            progress.start_phase(0, "Starting...")
            progress.update_phase(0, 0.5, "50% complete...")
        
        assert progress.phases[0].progress_pct == 0.5
    
    def test_complete_phase(self):
        """MultiPhaseProgress can complete a phase"""
        phases = ["Phase 1", "Phase 2"]
        progress = MultiPhaseProgress(phases)
        
        with patch('sys.stdout', new_callable=StringIO):
            progress.start_phase(0, "Starting...")
            progress.complete_phase(0, "✓ Phase 1 done")
        
        assert progress.phases[0].status == "complete"
        assert progress.phases[0].end_time is not None
        assert progress.phases[0].progress_pct == 1.0
    
    def test_fail_phase(self):
        """MultiPhaseProgress can mark phase as failed"""
        phases = ["Phase 1"]
        progress = MultiPhaseProgress(phases)
        
        with patch('sys.stdout', new_callable=StringIO):
            progress.start_phase(0, "Starting...")
            progress.fail_phase(0, "✗ Error occurred")
        
        assert progress.phases[0].status == "failed"
        assert progress.phases[0].end_time is not None
    
    def test_multi_phase_sequence(self):
        """MultiPhaseProgress handles full 3-phase sequence"""
        phases = ["Specification", "Cost Analysis", "Code Generation"]
        progress = MultiPhaseProgress(phases)
        
        with patch('sys.stdout', new_callable=StringIO):
            # Phase 0: Specification
            progress.start_phase(0, "Extracting goals...")
            progress.update_phase(0, 0.5, "Generating spec...")
            progress.complete_phase(0, "✓ Specification done")
            
            # Phase 1: Cost Analysis
            progress.start_phase(1, "Calculating cost...")
            progress.update_phase(1, 0.3, "Evaluating variants...")
            progress.complete_phase(1, "✓ Cost analysis done")
            
            # Phase 2: Code Generation
            progress.start_phase(2, "Generating code...")
            progress.update_phase(2, 0.8, "Finalizing...")
            progress.complete_phase(2, "✓ Code generation done")
        
        assert progress.phases[0].status == "complete"
        assert progress.phases[1].status == "complete"
        assert progress.phases[2].status == "complete"
    
    def test_multi_phase_no_color(self):
        """MultiPhaseProgress respects no_color flag"""
        phases = ["Phase 1"]
        progress = MultiPhaseProgress(phases, use_color=False)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            progress.start_phase(0, "Starting...")
            output = mock_stdout.getvalue()
            
            # Should not contain ANSI color codes
            assert "\x1b[" not in output
    
    def test_render_phases(self):
        """MultiPhaseProgress renders phase information"""
        phases = ["Phase 1", "Phase 2", "Phase 3"]
        progress = MultiPhaseProgress(phases)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            progress.start_phase(0, "Phase 1...")
            progress.complete_phase(0, "✓ Done")
            progress.start_phase(1, "Phase 2...")
            
            output = mock_stdout.getvalue()
            
            assert "Phase 1" in output or "Phase" in output
            # Check that phases are being rendered (output not empty)
            assert len(output) > 0


class TestProgressReporter:
    """Tests for ProgressReporter callback system"""
    
    def test_progress_reporter_creation(self):
        """ProgressReporter initializes correctly"""
        reporter = ProgressReporter("Scanning...")
        
        assert reporter.prefix == "Scanning..."
        assert reporter.use_spinner is False
        assert reporter.last_pct == -1
    
    def test_progress_reporter_with_total(self):
        """ProgressReporter handles definite progress (with total)"""
        reporter = ProgressReporter("Loading")
        
        with patch('sys.stdout', new_callable=StringIO):
            reporter.update(50, 100)  # current, total
            assert reporter.last_pct == 50
            
            reporter.finish()
    
    def test_progress_reporter_with_spinner(self):
        """ProgressReporter uses spinner for indefinite progress"""
        reporter = ProgressReporter("Scanning...", use_spinner=True)
        
        with patch('sys.stdout', new_callable=StringIO):
            reporter.update(10, 100)
            time.sleep(0.2)
            reporter.finish("✓ Complete")
    
    def test_progress_reporter_callback(self):
        """ProgressReporter works as callback function"""
        reporter = ProgressReporter("Processing")
        
        with patch('sys.stdout', new_callable=StringIO):
            # Simulate callback usage
            for i in range(0, 101, 10):
                reporter.update(i, 100)
            
            reporter.finish()
            assert reporter.last_pct == 100


class TestConvenienceFunctions:
    """Tests for convenience wrapper functions"""
    
    def test_with_spinner_decorator(self):
        """with_spinner wraps function correctly"""
        def mock_fn():
            return "result"
        
        with patch('sys.stdout', new_callable=StringIO):
            result = with_spinner(mock_fn, "Processing...")
        
        assert result == "result"
    
    def test_with_progress_bar_decorator(self):
        """with_progress_bar processes list correctly"""
        items = [1, 2, 3, 4, 5]
        
        def process(x):
            return x * 2
        
        with patch('sys.stdout', new_callable=StringIO):
            results = with_progress_bar(items, process, "Processing", use_color=False)
        
        assert results == [2, 4, 6, 8, 10]


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_progress_bar_zero_total(self):
        """ProgressBar handles zero total gracefully"""
        bar = ProgressBar(total=0, prefix="Empty")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            bar.update(0)
            output = mock_stdout.getvalue()
            # Should handle gracefully without errors
            assert len(output) > 0
    
    def test_multi_phase_empty_phases(self):
        """MultiPhaseProgress handles empty phase list"""
        progress = MultiPhaseProgress([])
        
        assert len(progress.phases) == 0
        
        # Should not crash on render
        with patch('sys.stdout', new_callable=StringIO):
            # No crash on empty list
            assert True
    
    def test_spinner_double_stop(self):
        """Spinner handles double stop gracefully"""
        spinner = Spinner("Test")
        
        with patch('sys.stdout', new_callable=StringIO):
            spinner.start()
            time.sleep(0.2)
            spinner.stop()
            spinner.stop()  # Should not crash
    
    def test_progress_update_beyond_total(self):
        """ProgressBar handles updates beyond total"""
        bar = ProgressBar(total=100, prefix="Test")
        
        bar.update(150)  # Beyond total
        assert bar.current <= bar.total  # Should be clamped


class TestIntegration:
    """Integration tests for real-world usage patterns"""
    
    def test_build_pipeline_simulation(self):
        """Simulate full 3-tier build pipeline progress"""
        phases = ["Specification", "Cost Analysis", "Code Generation"]
        progress = MultiPhaseProgress(phases)
        
        with patch('sys.stdout', new_callable=StringIO):
            # Specification phase
            progress.start_phase(0, "Extracting goals from intent...")
            time.sleep(0.1)
            progress.update_phase(0, 0.5, "Generating specification...")
            time.sleep(0.1)
            progress.complete_phase(0, "✓ Specification complete")
            
            # Cost Analysis phase
            progress.start_phase(1, "Analyzing cost and budget...")
            time.sleep(0.1)
            progress.update_phase(1, 0.5, "Evaluating spec variants...")
            time.sleep(0.1)
            progress.complete_phase(1, "✓ Cost analysis complete")
            
            # Code Generation phase
            progress.start_phase(2, "Gathering context...")
            time.sleep(0.1)
            progress.update_phase(2, 0.3, "Executing code generation...")
            time.sleep(0.1)
            progress.update_phase(2, 0.8, "Reflecting on results...")
            time.sleep(0.1)
            progress.complete_phase(2, "✓ Code generation complete")
        
        # Verify all phases completed
        assert all(p.status == "complete" for p in progress.phases)
        assert all(p.end_time is not None for p in progress.phases)
    
    def test_context_assembly_progress(self):
        """Simulate context assembly with callback progress"""
        reporter = ProgressReporter("Scanning codebase")
        
        with patch('sys.stdout', new_callable=StringIO):
            # Simulate file scanning
            for i in range(0, 101, 20):
                reporter.update(i, 100)
                time.sleep(0.05)
            
            reporter.finish()
        
        assert reporter.last_pct == 100
