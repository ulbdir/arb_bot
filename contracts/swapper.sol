//SPDX-License-Identifier: MIT
pragma solidity >= 0.8.0;

import "./IERC20.sol";
import "./Ownable.sol";
import "./IUniswapV2Router01.sol";

// see https://ftmscan.com/address/0x6eC7f156d2747A061A3DDC2D0a1B67d64C94E0B0#code
// see https://github.com/paco0x/amm-arbitrageur/blob/master/contracts/FlashBot.sol
// see https://ftmscan.com/address/0x4614b22722e8fd12ae5ee131d1a14f449849a64f#code

import "hardhat/console.sol";

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
        token_wftm.transfer(msg.sender, _balance_after_swap);
    }

    function swap(address _router, address _token_in, address _token_out, uint _amount_in) private returns (uint) {
        address[] memory path = new address[](2);
        path[0] = _token_in;
        path[1] = _token_out;

        // approve _router to deduct _amount_in of _token_in from this contract
        IERC20(_token_in).approve(_router, _amount_in);

        // set deadline to 1h
        uint deadline = block.timestamp + 3600;

        uint amount_received = IUniswapV2Router01(_router).swapExactTokensForTokens(_amount_in, 0, path, address(this), deadline)[1];
        return amount_received;
    }

    function buy(address _router, address _token, uint _amount) private returns(uint) {
        console.log("buy token %s with amount %s", _token, _amount);
        uint amount_received = swap(_router, wftm, _token, _amount);
        return amount_received;
    }

    function sell(address _router, address _token, uint _amount) private returns (uint) {
        console.log("buy token %s with amount %s", _token, _amount);
        uint amount_received = swap(_router, _token, wftm, _amount);
        return amount_received;
    }

    receive() external payable {
    }

    // View token balance of contract, in case anything went wrong. Should never be needed.
    function getBalance (address tc1) external view  returns (uint256) {
        uint balance = IERC20(tc1).balanceOf(address(this));
        return balance;
    }

    // withdraw all FTM to owner. Should never be needed.
    function withdrawNative() external onlyOwner {
        payable(msg.sender).transfer(address(this).balance);
    }

    // Withdraw all _token to owner. Should never be needed.
    function withdrawTokens(address _token) external onlyOwner {
        IERC20 token = IERC20(_token);
        token.transfer(msg.sender, token.balanceOf(address(this)));
    }
}


