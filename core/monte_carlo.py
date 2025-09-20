import json
import logging
from typing import Dict, Any, List, Optional

# Optional imports for scientific computing
try:
    import numpy as np
    import scipy.stats as stats
    HAS_SCIENTIFIC_LIBS = True
except ImportError:
    HAS_SCIENTIFIC_LIBS = False
    np = None
    stats = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monte_carlo_sim(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monte Carlo simulation for risk analysis with real implementation.
    
    Args:
        project_data: Dictionary containing project data with base_cost, profit, and vars
        
    Returns:
        Simulation results with statistics and histogram bins
    """
    # Check if required libraries are available
    if not HAS_SCIENTIFIC_LIBS:
        return {
            "status": "error",
            "error": "Required scientific libraries (numpy, scipy) not available. Please install them."
        }
    
    try:
        # Extract parameters
        base_cost = project_data.get("base_cost", 200e6)  # 200 million
        profit = project_data.get("profit", 300e6)  # 300 million
        variables = project_data.get("vars", {
            "cost": 0.2,    # 20% variance
            "time": 0.15,   # 15% variance
            "roi": 0.1      # 10% variance
        })
        
        # Simulation parameters
        n_simulations = 10000  # Increased for better accuracy
        
        # Generate random samples
        cost_variance = variables.get("cost", 0.2)
        time_variance = variables.get("time", 0.15)
        roi_variance = variables.get("roi", 0.1)
        
        # Generate cost simulations with log-normal distribution for better realism
        # Log-normal distribution is more appropriate for costs as they cannot be negative
        cost_mu = np.log(base_cost) - 0.5 * cost_variance**2
        cost_sim = np.random.lognormal(cost_mu, cost_variance, n_simulations)
        
        # Generate profit simulations (correlated with costs)
        # Assuming profit is somewhat correlated with costs but with its own variance
        # Using a more sophisticated approach with correlation
        correlation = 0.3  # Moderate correlation between cost and profit
        profit_std = profit * roi_variance
        
        # Generate correlated random variables
        cov_matrix = np.array([[cost_variance**2, correlation * cost_variance * profit_std],
                              [correlation * cost_variance * profit_std, profit_std**2]])
        
        # Generate correlated samples
        correlated_samples = np.random.multivariate_normal([0, 0], cov_matrix, n_simulations)
        profit_sim = profit * np.exp(correlated_samples[:, 1])
        
        # Calculate ROI for each simulation
        # ROI = (profit - cost) / cost
        roi_sim = (profit_sim - cost_sim) / cost_sim
        
        # Calculate Net Present Value (NPV) with discount rate
        discount_rate = project_data.get("discount_rate", 0.05)  # 5% default
        project_duration = project_data.get("duration_years", 2.0)  # 2 years default
        
        # Calculate NPV for each simulation
        npv_sim = []
        for i in range(n_simulations):
            # Simple NPV calculation over project duration
            cash_flows = [-cost_sim[i]] + [profit_sim[i] / project_duration] * int(project_duration)
            npv = np.npv(discount_rate, cash_flows)
            npv_sim.append(npv)
        npv_sim = np.array(npv_sim)
        
        # Calculate Internal Rate of Return (IRR)
        irr_sim = []
        for i in range(min(1000, n_simulations)):  # Limit IRR calculations for performance
            cash_flows = [-cost_sim[i]] + [profit_sim[i] / project_duration] * int(project_duration)
            try:
                irr = np.irr(cash_flows)
                irr_sim.append(irr if not np.isnan(irr) else 0)
            except:
                irr_sim.append(0)
        irr_sim = np.array(irr_sim)
        
        # Calculate statistics
        mean_roi = np.mean(roi_sim)
        std_roi = np.std(roi_sim)
        
        # Calculate percentiles
        p10_roi = np.percentile(roi_sim, 10)
        p50_roi = np.percentile(roi_sim, 50)  # Median
        p90_roi = np.percentile(roi_sim, 90)
        
        # Create histogram bins for Recharts
        hist_bins = np.histogram(roi_sim, bins=50, range=(0, 1.0))[0].tolist()
        bin_edges = np.histogram(roi_sim, bins=50, range=(0, 1.0))[1].tolist()
        
        # Create bin labels for charting
        bin_labels = []
        for i in range(len(bin_edges) - 1):
            bin_labels.append((bin_edges[i] + bin_edges[i+1]) / 2)
        
        # Additional statistics
        mean_profit = np.mean(profit_sim)
        std_profit = np.std(profit_sim)
        mean_cost = np.mean(cost_sim)
        std_cost = np.std(cost_sim)
        mean_npv = np.mean(npv_sim)
        std_npv = np.std(npv_sim)
        
        # Calculate probability of positive ROI
        positive_roi_prob = np.sum(roi_sim > 0) / n_simulations
        
        # Calculate probability of positive NPV
        positive_npv_prob = np.sum(npv_sim > 0) / n_simulations
        
        # Calculate Value at Risk (VaR) at 5%
        var_5 = np.percentile(roi_sim, 5)
        
        # Calculate Expected Shortfall (Conditional VaR)
        es_5 = np.mean(roi_sim[roi_sim <= var_5])
        
        results = {
            "status": "success",
            "simulation_count": n_simulations,
            "base_cost": base_cost,
            "base_profit": profit,
            "discount_rate": discount_rate,
            "project_duration": project_duration,
            "variables": variables,
            "roi_statistics": {
                "mean": float(mean_roi),
                "std": float(std_roi),
                "p10": float(p10_roi),
                "p50": float(p50_roi),
                "p90": float(p90_roi),
                "positive_probability": float(positive_roi_prob),
                "var_5": float(var_5),
                "expected_shortfall_5": float(es_5)
            },
            "npv_statistics": {
                "mean": float(mean_npv),
                "std": float(std_npv),
                "positive_probability": float(positive_npv_prob)
            },
            "profit_statistics": {
                "mean": float(mean_profit),
                "std": float(std_profit)
            },
            "cost_statistics": {
                "mean": float(mean_cost),
                "std": float(std_cost)
            },
            "histogram": {
                "bins": hist_bins,
                "bin_centers": [float(x) for x in bin_labels],
                "bin_edges": [float(x) for x in bin_edges]
            },
            "confidence": 0.95  # Increased confidence level
        }
        
        # Add IRR statistics if calculated
        if len(irr_sim) > 0:
            results["irr_statistics"] = {
                "mean": float(np.mean(irr_sim)),
                "std": float(np.std(irr_sim)),
                "p10": float(np.percentile(irr_sim, 10)),
                "p50": float(np.percentile(irr_sim, 50)),
                "p90": float(np.percentile(irr_sim, 90))
            }
        
        logger.info(f"Monte Carlo simulation completed with {n_simulations} simulations")
        logger.info(f"Mean ROI: {mean_roi:.2%}, Std: {std_roi:.2%}")
        logger.info(f"P10: {p10_roi:.2%}, P90: {p90_roi:.2%}")
        logger.info(f"Mean NPV: {mean_npv:,.0f} RUB, Positive NPV Probability: {positive_npv_prob:.2%}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in Monte Carlo simulation: {str(e)}")
        return {
            "status": "error",
            "error": f"Monte Carlo simulation failed: {str(e)}"
        }

def _calculate_correlation_matrix(roi_sim: np.ndarray, cost_sim: np.ndarray, profit_sim: np.ndarray) -> Dict[str, Any]:
    """
    Calculate correlation matrix between variables.
    
    Args:
        roi_sim: ROI simulations
        cost_sim: Cost simulations
        profit_sim: Profit simulations
        
    Returns:
        Correlation matrix
    """
    # Check if required libraries are available
    if not HAS_SCIENTIFIC_LIBS:
        return {
            "roi_cost": 0.0,
            "roi_profit": 0.0,
            "cost_profit": 0.0
        }
    
    data = np.column_stack([roi_sim, cost_sim, profit_sim])
    corr_matrix = np.corrcoef(data, rowvar=False)
    
    return {
        "roi_cost": float(corr_matrix[0, 1]),
        "roi_profit": float(corr_matrix[0, 2]),
        "cost_profit": float(corr_matrix[1, 2])
    }

# Example usage
if __name__ == "__main__":
    # Test with sample data
    sample_data = {
        "base_cost": 200e6,
        "profit": 300e6,
        "discount_rate": 0.05,
        "duration_years": 2.0,
        "vars": {
            "cost": 0.2,
            "time": 0.15,
            "roi": 0.1
        }
    }
    
    result = monte_carlo_sim(sample_data)
    print(json.dumps(result, indent=2, ensure_ascii=False))