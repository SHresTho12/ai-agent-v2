import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

# Adjust this import based on your actual project structure
from src.tool_caller.tools.system_info_tool import SystemInfoTool


class TestSystemInfoToolSimple:
    """Simple tests for SystemInfoTool"""
    
    @pytest.fixture
    def tool(self):
        """Create a SystemInfoTool instance for testing"""
        return SystemInfoTool()
    
    def test_tool_name_and_description(self, tool):
        """Test that tool has correct name and description"""
        assert tool.name == "system_info"
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0
    
    def test_tool_schema(self, tool):
        """Test tool schema properties"""
        schema = tool.schema
        assert schema.name == "system_info"
        assert hasattr(schema, 'parameters')
        assert schema.parameters["type"] == "object"
        assert "properties" in schema.parameters
    
    def test_validate_parameters_empty(self, tool):
        """Test validation with empty parameters"""
        assert tool.validate_parameters({}) is True
    
    def test_validate_parameters_valid_boolean(self, tool):
        """Test validation with valid boolean parameters"""
        params = {"include_processes": True, "include_network": False}
        assert tool.validate_parameters(params) is True
    
    def test_validate_parameters_valid_integer(self, tool):
        """Test validation with valid integer parameter"""
        params = {"top_processes": 10}
        assert tool.validate_parameters(params) is True
    
    def test_validate_parameters_invalid_boolean(self, tool):
        """Test validation with invalid boolean"""
        params = {"include_processes": "not_a_boolean"}
        assert tool.validate_parameters(params) is False
    
    def test_validate_parameters_invalid_integer(self, tool):
        """Test validation with invalid integer"""
        params = {"top_processes": "not_a_number"}
        assert tool.validate_parameters(params) is False
        
        params = {"top_processes": -1}
        assert tool.validate_parameters(params) is False
        
        params = {"top_processes": 0}
        assert tool.validate_parameters(params) is False
    
    def test_get_size_bytes(self, tool):
        """Test byte size conversion for small values"""
        assert tool._get_size(0) == "0.00 B"
        assert tool._get_size(500) == "500.00 B"
        assert tool._get_size(1023) == "1023.00 B"
    
    def test_get_size_kilobytes(self, tool):
        """Test byte size conversion for KB values"""
        assert tool._get_size(1024) == "1.00 KB"
        assert tool._get_size(2048) == "2.00 KB"
        assert "KB" in tool._get_size(1500)
    
    def test_get_size_megabytes(self, tool):
        """Test byte size conversion for MB values"""
        mb = 1024 * 1024
        assert tool._get_size(mb) == "1.00 MB"
        assert tool._get_size(mb * 5) == "5.00 MB"
    
    def test_get_size_gigabytes(self, tool):
        """Test byte size conversion for GB values"""
        gb = 1024 * 1024 * 1024
        assert tool._get_size(gb) == "1.00 GB"
        assert tool._get_size(gb * 2) == "2.00 GB"


class TestSystemInfoToolAsync:
    """Async tests for SystemInfoTool"""
    
    @pytest.fixture
    def tool(self):
        return SystemInfoTool()
    
    @pytest.mark.asyncio
    async def test_run_minimal_mocking(self, tool):
        """Test _run method with minimal mocking"""
        with patch('src.tool_caller.tools.system_info_tool.platform') as mock_platform, \
             patch('src.tool_caller.tools.system_info_tool.psutil') as mock_psutil:
            
            # Mock platform
            mock_platform.system.return_value = "Linux"
            mock_platform.node.return_value = "test-node"
            mock_platform.release.return_value = "5.4.0"
            mock_platform.version.return_value = "Ubuntu 20.04"
            mock_platform.machine.return_value = "x86_64"
            mock_platform.processor.return_value = "Intel i7"
            mock_platform.python_version.return_value = "3.9.0"
            
            # Mock psutil - CPU
            mock_psutil.cpu_count.return_value = 4  # Will be called twice
            mock_psutil.cpu_percent.return_value = 25.0
            mock_psutil.boot_time.return_value = 1640995200.0
            
            # Mock CPU frequency
            mock_freq = Mock()
            mock_freq.current = 2400.0
            mock_freq.min = 1000.0
            mock_freq.max = 3000.0
            mock_psutil.cpu_freq.return_value = mock_freq
            
            # Mock memory
            mock_memory = Mock()
            mock_memory.total = 8 * 1024 * 1024 * 1024  # 8GB
            mock_memory.available = 4 * 1024 * 1024 * 1024  # 4GB
            mock_memory.used = 4 * 1024 * 1024 * 1024  # 4GB
            mock_memory.percent = 50.0
            mock_psutil.virtual_memory.return_value = mock_memory
            
            # Mock swap
            mock_swap = Mock()
            mock_swap.total = 2 * 1024 * 1024 * 1024
            mock_swap.used = 1 * 1024 * 1024 * 1024
            mock_swap.free = 1 * 1024 * 1024 * 1024
            mock_swap.percent = 25.0
            mock_psutil.swap_memory.return_value = mock_swap
            
            # Mock disk
            mock_partition = Mock()
            mock_partition.device = "/dev/sda1"
            mock_partition.mountpoint = "/"
            mock_partition.fstype = "ext4"
            mock_psutil.disk_partitions.return_value = [mock_partition]
            
            mock_disk_usage = Mock()
            mock_disk_usage.total = 100 * 1024 * 1024 * 1024
            mock_disk_usage.used = 50 * 1024 * 1024 * 1024
            mock_disk_usage.free = 50 * 1024 * 1024 * 1024
            mock_psutil.disk_usage.return_value = mock_disk_usage
            
            # Mock network
            mock_net = Mock()
            mock_net.bytes_sent = 1024 * 1024
            mock_net.bytes_recv = 2 * 1024 * 1024
            mock_net.packets_sent = 1000
            mock_net.packets_recv = 2000
            mock_net.errin = 0
            mock_net.errout = 0
            mock_net.dropin = 0
            mock_net.dropout = 0
            mock_psutil.net_io_counters.return_value = mock_net
            
            # Run the method
            result = await tool._run()
            
            # Check basic structure
            assert isinstance(result, dict)
            assert "timestamp" in result
            assert "system" in result
            assert "cpu" in result
            assert "memory" in result
            assert "disks" in result
            assert "network" in result
            assert "processing_time_seconds" in result
    
    @pytest.mark.asyncio
    async def test_run_without_network(self, tool):
        """Test _run method without network information"""
        with patch('src.tool_caller.tools.system_info_tool.platform') as mock_platform, \
             patch('src.tool_caller.tools.system_info_tool.psutil') as mock_psutil:
            
            # Setup minimal mocks
            self._setup_minimal_mocks(mock_platform, mock_psutil)
            
            # Run without network
            result = await tool._run(include_network=False)
            
            # Should not include network
            assert "network" not in result
            assert "system" in result
            assert "cpu" in result
    
    @pytest.mark.asyncio
    async def test_run_with_processes(self, tool):
        """Test _run method with process information"""
        with patch('src.tool_caller.tools.system_info_tool.platform') as mock_platform, \
             patch('src.tool_caller.tools.system_info_tool.psutil') as mock_psutil:
            
            # Setup minimal mocks
            self._setup_minimal_mocks(mock_platform, mock_psutil)
            
            # Mock processes
            mock_proc = Mock()
            mock_proc.info = {
                'pid': 1234, 
                'name': 'python', 
                'cpu_percent': 15.5, 
                'memory_percent': 25.0
            }
            mock_psutil.process_iter.return_value = [mock_proc]
            
            # Run with processes
            result = await tool._run(include_processes=True, top_processes=5)
            
            # Should include processes
            assert "processes" in result
            assert "top_cpu" in result["processes"]
            assert "top_memory" in result["processes"]
            assert "total_processes" in result["processes"]
    
    @pytest.mark.asyncio
    async def test_run_handles_exceptions(self, tool):
        """Test that _run handles exceptions properly"""
        with patch('src.tool_caller.tools.system_info_tool.platform') as mock_platform:
            # Make platform.system() raise an exception
            mock_platform.system.side_effect = Exception("Test error")
            
            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="Failed to gather system information"):
                await tool._run()
    
    def _setup_minimal_mocks(self, mock_platform, mock_psutil):
        """Helper to set up minimal mocks that won't fail"""
        # Platform
        mock_platform.system.return_value = "Linux"
        mock_platform.node.return_value = "test"
        mock_platform.release.return_value = "1.0"
        mock_platform.version.return_value = "Test OS"
        mock_platform.machine.return_value = "x86_64"
        mock_platform.processor.return_value = "Test CPU"
        mock_platform.python_version.return_value = "3.9.0"
        
        # CPU
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.boot_time.return_value = 1640995200.0
        mock_psutil.cpu_freq.return_value = None  # Some systems don't have this
        
        # Memory
        mock_memory = Mock()
        mock_memory.total = 8 * 1024 * 1024 * 1024
        mock_memory.available = 4 * 1024 * 1024 * 1024
        mock_memory.used = 4 * 1024 * 1024 * 1024
        mock_memory.percent = 50.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_swap = Mock()
        mock_swap.total = 0  # No swap
        mock_swap.used = 0
        mock_swap.free = 0
        mock_swap.percent = 0.0
        mock_psutil.swap_memory.return_value = mock_swap
        
        # Disk
        mock_psutil.disk_partitions.return_value = []  # No disks for simplicity
        
        # Network
        mock_net = Mock()
        mock_net.bytes_sent = 1024
        mock_net.bytes_recv = 2048
        mock_net.packets_sent = 10
        mock_net.packets_recv = 20
        mock_net.errin = 0
        mock_net.errout = 0
        mock_net.dropin = 0
        mock_net.dropout = 0
        mock_psutil.net_io_counters.return_value = mock_net


# Simple integration test that doesn't require mocking
class TestSystemInfoRealSystem:
    """Very basic real system test - only run if you want to test against actual system"""
    
    @pytest.fixture
    def tool(self):
        return SystemInfoTool()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_system_basic_structure(self, tool):
        """Test basic structure with real system - mark as integration test"""
        # This will run against your actual system
        # Only run this test with: pytest -m integration
        
        result = await tool._run()
        
        # Just check that we get the expected structure
        assert isinstance(result, dict)
        assert "system" in result
        assert "cpu" in result
        assert "memory" in result
        
        # Check that we got real values (not mocked)
        assert isinstance(result["cpu"]["physical_cores"], int)
        assert result["cpu"]["physical_cores"] > 0


if __name__ == "__main__":
    # Run just the non-integration tests
    pytest.main([__file__, "-v", "-m", "not integration"])