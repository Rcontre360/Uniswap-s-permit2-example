import {ethers} from "hardhat";
import {expect} from "chai";
import {PermitTransferFrom, SignatureTransfer} from "@uniswap/permit2-sdk";
import {BigNumberish, Contract, Signer} from "ethers";
import {MockERC20, Permit2, Permit2Vault} from "../typechain-types";

const deploy = async <T extends Contract>(contract: string, signer: Signer, args: any[]) => {
  const factory = await ethers.getContractFactory(contract);
  return (await factory.connect(signer).deploy(...args)) as T;
};

const depositAmount = ethers.utils.parseEther("10");

describe("Permit2 test", function () {
  it("should deposit on vault", async () => {
    const [signer] = await ethers.getSigners();
    const permit: Permit2 = await deploy("Permit2", signer, []);
    const vault: Permit2Vault = await deploy("Permit2Vault", signer, [permit.address]); //we fork eth network for this test
    const token: MockERC20 = await deploy("MockERC20", signer, []);

    const block = await ethers.provider.getBlock("latest");
    const chainId = (await ethers.provider.getNetwork()).chainId;
    const nonce = (await permit.allowance(signer.address, token.address, vault.address)).expiration;

    await token.mint(signer.address, depositAmount);
    await token.approve(permit.address, depositAmount);

    const message: Omit<PermitTransferFrom, "spender"> = {
      permitted: {
        token: token.address,
        amount: depositAmount,
      },
      nonce,
      deadline: block.timestamp + 10000000,
      //spender: vault.address,
    };

    const {domain, types, values} = SignatureTransfer.getPermitData(
      {...message, spender: vault.address},
      permit.address,
      chainId
    );
    const signature = await signer._signTypedData(domain, types, values);

    await vault.connect(signer).depositERC20(token.address, depositAmount, message, signature);
  });
});
