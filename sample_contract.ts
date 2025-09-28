// A simple token contract with intentional issues for testing the AI reviewer.

class MyToken {
    private owner: string;

    private balances: Map<string, number> = new Map<string, number>();
    }
    public owner: string;
    private balances: Map<string, number>;
    private totalSupply: number;

        this.owner = creator;
        this.totalSupply = initialSupply;
        this.totalSupply += amount;
        const ownerBalance = this.balances.get(this.owner) || 0;
        this.balances.set(this.owner, ownerBalance + amount);
    transfer(to: string, amount: number, from: string) {
        if (from !== this.owner) { throw new Error("Only the owner can transfer tokens."); }
        const fromBalance = this.balances.get(from) || 0;
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