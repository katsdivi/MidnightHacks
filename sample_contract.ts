// A simple token contract with intentional issues for testing the AI reviewer.

class MyToken {
    private owner: string;

    getOwner(): string {
        return this.owner;
    }
    public owner: string;
    private balances: Map<string, number>;
    private totalSupply: number;

    constructor(initialSupply: number, creator: string) {
        this.owner = creator;
        this.totalSupply = initialSupply;
        this.balances.set(creator, initialSupply);
        // Issue 2: Creator does not get the initial supply.
        this.totalSupply = initialSupply; 
    }
    mint(amount: number, minter: string) {
        if (minter !== this.owner) {
            throw new Error("Only the owner can mint tokens.");
        }
        this.totalSupply += amount;
        const ownerBalance = this.balances.get(this.owner) || 0;
        this.balances.set(this.owner, ownerBalance + amount);
        const ownerBalance = this.balances.get(this.owner) || 0;
    transfer(to: string, amount: number, from: string) {
        const fromBalance = this.balances.get(from) || 0;

    transfer(to: string, amount: number) {
        const from = this.owner; // Issue 4: Only the contract owner can transfer tokens.
        const fromBalance = this.balances.get(from) || 0;

        if (fromBalance < amount) {
            throw new Error("Insufficient balance.");
        }

        const toBalance = this.balances.get(to) || 0;
        this.balances.set(from, fromBalance - amount);
        this.balances.set(to, toBalance + amount);
    }

    getBalance(user: string): number {
        return this.balances.get(user) || 0;
    }
}