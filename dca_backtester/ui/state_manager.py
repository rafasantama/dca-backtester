"""Streamlit state management for live execution wizard."""

import streamlit as st
import json
from pathlib import Path
from typing import Optional, Dict, Any


class WizardState:
    """Manage wizard state across sessions."""
    
    STATE_FILE = Path("wizard_state.json")
    
    @staticmethod
    def save_state(key: str, data: Dict[str, Any]) -> None:
        """Persist state to session_state and local JSON."""
        # Save to session state
        st.session_state[key] = data
        
        # Save to local file for persistence
        try:
            if WizardState.STATE_FILE.exists():
                existing = json.loads(WizardState.STATE_FILE.read_text())
            else:
                existing = {}
                
            existing[key] = data
            WizardState.STATE_FILE.write_text(json.dumps(existing, indent=2))
            
        except Exception as e:
            st.warning(f"Could not persist state: {e}")
        
    @staticmethod
    def load_state(key: str) -> Optional[Dict[str, Any]]:
        """Load state from session_state or local JSON."""
        # First check session state
        if key in st.session_state:
            return st.session_state[key]
        
        # Then check local file
        try:
            if WizardState.STATE_FILE.exists():
                data = json.loads(WizardState.STATE_FILE.read_text())
                state = data.get(key)
                if state:
                    # Load into session state for future access
                    st.session_state[key] = state
                return state
        except Exception as e:
            st.warning(f"Could not load state: {e}")
            
        return None
        
    @staticmethod
    def clear_state(key: str) -> None:
        """Clear state from both session and file."""
        # Clear from session state
        if key in st.session_state:
            del st.session_state[key]
            
        # Clear from file
        try:
            if WizardState.STATE_FILE.exists():
                data = json.loads(WizardState.STATE_FILE.read_text())
                if key in data:
                    del data[key]
                    WizardState.STATE_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            st.warning(f"Could not clear state: {e}")
            
    @staticmethod
    def get_all_keys() -> list:
        """Get all available state keys."""
        keys = set()
        
        # From session state
        for key in st.session_state.keys():
            if not key.startswith('_'):  # Skip Streamlit internal keys
                keys.add(key)
                
        # From file
        try:
            if WizardState.STATE_FILE.exists():
                data = json.loads(WizardState.STATE_FILE.read_text())
                keys.update(data.keys())
        except Exception:
            pass
            
        return list(keys)


class LiveExecutionState:
    """Specific state management for live execution workflow."""
    
    WALLET_STATE_KEY = "live_wallet_state"
    PLAN_STATE_KEY = "live_plan_state"
    EXECUTION_STATE_KEY = "live_execution_state"
    
    @staticmethod
    def save_wallet_state(wallet_address: str, network: str) -> None:
        """Save wallet connection state."""
        WizardState.save_state(LiveExecutionState.WALLET_STATE_KEY, {
            "wallet_address": wallet_address,
            "network": network,
            "connected_at": str(st.session_state.get("current_time", "unknown"))
        })
        
    @staticmethod
    def load_wallet_state() -> Optional[Dict[str, Any]]:
        """Load wallet connection state."""
        return WizardState.load_state(LiveExecutionState.WALLET_STATE_KEY)
        
    @staticmethod
    def save_plan_state(plan_data: Dict[str, Any]) -> None:
        """Save DCA plan configuration."""
        WizardState.save_state(LiveExecutionState.PLAN_STATE_KEY, plan_data)
        
    @staticmethod
    def load_plan_state() -> Optional[Dict[str, Any]]:
        """Load DCA plan configuration."""
        return WizardState.load_state(LiveExecutionState.PLAN_STATE_KEY)
        
    @staticmethod
    def save_execution_state(execution_data: Dict[str, Any]) -> None:
        """Save execution status and history."""
        WizardState.save_state(LiveExecutionState.EXECUTION_STATE_KEY, execution_data)
        
    @staticmethod
    def load_execution_state() -> Optional[Dict[str, Any]]:
        """Load execution status and history."""
        return WizardState.load_state(LiveExecutionState.EXECUTION_STATE_KEY)
        
    @staticmethod
    def clear_all_state() -> None:
        """Clear all live execution state."""
        WizardState.clear_state(LiveExecutionState.WALLET_STATE_KEY)
        WizardState.clear_state(LiveExecutionState.PLAN_STATE_KEY)
        WizardState.clear_state(LiveExecutionState.EXECUTION_STATE_KEY)
        
    @staticmethod
    def is_wallet_connected() -> bool:
        """Check if wallet is connected."""
        wallet_state = LiveExecutionState.load_wallet_state()
        return wallet_state is not None and "wallet_address" in wallet_state
        
    @staticmethod
    def get_connected_wallet() -> Optional[str]:
        """Get connected wallet address."""
        wallet_state = LiveExecutionState.load_wallet_state()
        if wallet_state:
            return wallet_state.get("wallet_address")
        return None