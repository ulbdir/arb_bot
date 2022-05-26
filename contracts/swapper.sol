//SPDX-License-Identifier: MIT
pragma solidity >= 0.8.0;

import "./IERC20.sol";
import "./Ownable.sol";
import "./IUniswapV2Router01.sol";

contract Swapper is Ownable {

    // address of WFTM Token
    address private wftm = 0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83;

    // transfer wftm from wallet to contract
    // swap WFTM for token at r1
    // swapp token for WFTM at r2
    // check if swap was profitable
    //  a) not profitable: revert tx
    //  b) profitable: send wftm back to wallet
    function multiswap(address r1, address r2, address token, uint256 amount) external onlyOwner {
        
        IERC20 token_wftm = IERC20(wftm);
    
        // transfer the WFTM from the wallet to the contract
        token_wftm.transferFrom(msg.sender, address(this), amount);
    
        // keep track of initial balance of wftm
        uint _balance_initial = token_wftm.balanceOf(address(this));
        
        // do the buying and selling of the token
        uint _amount = buy(r1, token, amount);
        sell(r2, token, _amount);

        // check new balance of wftm
        uint _balance_after_swap = token_wftm.balanceOf(address(this));

        // revert tx if the swap was not profitable
        require(_balance_after_swap > _balance_initial, "Not profitable");

        // transfer WFTM back to wallet
        token_wftm.transferFrom(address(this), msg.sender, _balance_after_swap);
    }

    function buy(address _router, address _token, uint _amount) private returns(uint256) {
        IERC20 token_wftm = IERC20(wftm);
        IERC20 token_swap = IERC20(_token);

        // approve _router to deduct _amount of _wftm from this contract
        IERC20(token_wftm).approve(_router, _amount);
    }

    function sell(address _router, address _token, uint _amount) private {
        IERC20 token_wftm = IERC20(wftm);
        IERC20 token_swap = IERC20(_token);

        // approve _router to deduct _amount of _token from this contract
        IERC20(_token).approve(_router, _amount);
    }

    receive() external payable {
    }

    // View token balance of contract, in case anything went wrong. Should never be needed.
    function getBalance (address tc1) external view  returns (uint256) {
        uint balance = IERC20(tc1).balanceOf(address(this));
        return balance;
    }

    // withdraw FTM to owner. Should never be needed.
    function withdrawNative() external onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }

    // Withdraw token to owner. Should never be needed.
    function withdrawTokens(address t1) external onlyOwner {
        IERC20 token = IERC20(t1);
        token.transfer(msg.sender, token.balanceOf(address(this)));
    }


}


