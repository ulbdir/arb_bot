//SPDX-License-Identifier: MIT
pragma solidity >= 0.8.0;

import "./IERC20.sol";
import "./Ownable.sol";
import "./IUniswapV2Router01.sol";

// see https://ftmscan.com/address/0x6eC7f156d2747A061A3DDC2D0a1B67d64C94E0B0#code
// see https://github.com/paco0x/amm-arbitrageur/blob/master/contracts/FlashBot.sol
// see https://ftmscan.com/address/0x4614b22722e8fd12ae5ee131d1a14f449849a64f#code

contract Swapper is Ownable {

    // address of WFTM Token
    address private wftm = 0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83;


    // This contract needs to be pre-approved to withdraw wftm from the caller!
    // 1. transfer wftm from wallet to contract
    // 2. swap WFTM for token at r1
    // 3. swapp token for WFTM at r2
    // 4. check if swap was profitable
    //  a) if not profitable: revert tx
    //  b) if profitable: send wftm back to wallet
    function multiswap(address r1, address r2, address token, uint256 amount) external onlyOwner {
        
        IERC20 token_wftm = IERC20(wftm);
    
        // 1. transfer the WFTM from the wallet to the contract
        token_wftm.transferFrom(msg.sender, address(this), amount);
    
        // keep track of initial balance of wftm
        uint _balance_initial = token_wftm.balanceOf(address(this));
        
        // 2. swap wftm for token at r1
        uint _amount = buy(r1, token, amount);
        
        // 3. swap token for wftm at r2
        sell(r2, token, _amount);

        // check new balance of wftm
        uint _balance_after_swap = token_wftm.balanceOf(address(this));

        // 4.a) revert tx if the swap was not profitable
        require(_balance_after_swap > _balance_initial, "Not profitable");

        // 4.b) transfer WFTM back to wallet
        token_wftm.transferFrom(address(this), msg.sender, _balance_after_swap);
    }

    function buy(address _router, address _token, uint _amount) private returns(uint256) {
        IERC20 token_wftm = IERC20(wftm);
        IERC20 token_swap = IERC20(_token);

        // approve _router to deduct _amount of _wftm from this contract
        IERC20(token_wftm).approve(_router, _amount);

        // TODO: use uniswap router interface to execute the swap
    }

    function sell(address _router, address _token, uint _amount) private {
        IERC20 token_wftm = IERC20(wftm);
        IERC20 token_swap = IERC20(_token);

        // approve _router to deduct _amount of _token from this contract
        IERC20(_token).approve(_router, _amount);

        // TODO: use uniswap router interface to execute the swap
    }

    // this contract can receive ftm. Just in case.
    receive() external payable {
    }

    // View token balance of contract, in case anything went wrong. Should never be needed,
    // since the tx is either reverted or the wftm is sent back to the caller.
    function get_balance (address _token) external view  returns (uint256) {
        uint balance = IERC20(_token).balanceOf(address(this));
        return balance;
    }

    // withdraw FTM to owner. Should never be needed.
    function withdraw() external onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }

    // Withdraw token to owner. Should never be needed.
    function withdraw_tokens(address _token) external onlyOwner {
        IERC20 token = IERC20(_token);
        token.transfer(msg.sender, token.balanceOf(address(this)));
    }
}


