from flask import Flask, render_template, request, redirect, url_for, flash
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# In-memory storage for piggy banks
# Structure: { 'bank_name': {'0.25': count, '0.10': count, '0.05': count, 'emoji': str, 'note': str} }
piggy_banks = {}
transfer_history = {}

@app.route('/')
def index():
    return render_template('index.html', piggy_banks=piggy_banks)

@app.route('/create_bank', methods=['POST'])
def create_bank():
    bank_name = request.form.get('bank_name')
    emoji = request.form.get('emoji', '')
    note = request.form.get('note', '')
    try:
        transfer_limit = float(request.form.get('transfer_limit', 10.0))
    except ValueError:
        transfer_limit = 10.0
    if bank_name and bank_name not in piggy_banks:
        piggy_banks[bank_name] = {
            '0.25': 0,
            '0.10': 0,
            '0.05': 0,
            'emoji': emoji,
            'note': note,
            'transfer_limit': transfer_limit
        }
    return redirect(url_for('index'))

@app.route('/add_coin', methods=['POST'])
def add_coin():
    bank_name = request.form.get('bank_name')
    denomination = request.form.get('denomination')
    if bank_name in piggy_banks and denomination in ['0.25', '0.10', '0.05']:
        piggy_banks[bank_name][denomination] += 1
    return redirect(url_for('index'))

@app.route('/withdraw', methods=['POST'])
def withdraw():
    bank_name = request.form.get('bank_name')
    try:
        amount = float(request.form.get('amount'))
    except (TypeError, ValueError):
        flash('Invalid withdrawal amount.')
        return redirect(url_for('index'))

    if bank_name not in piggy_banks or amount <= 0:
        flash('Invalid bank or amount.')
        return redirect(url_for('index'))

    coins = piggy_banks[bank_name]
    total = coins['0.25']*0.25 + coins['0.10']*0.10 + coins['0.05']*0.05

    if amount > total:
        flash('Withdrawal amount exceeds current balance.')
        return redirect(url_for('index'))

    # Greedy algorithm to withdraw using largest coins first
    remaining = round(amount, 2)
    for denom in ['0.25', '0.10', '0.05']:
        coin_value = float(denom)
        max_coins = min(coins[denom], int(remaining // coin_value))
        coins[denom] -= max_coins
        remaining -= round(max_coins * coin_value, 2)

    # If not able to make exact change, rollback and show error
    if abs(remaining) > 0.001:
        # Rollback: add coins back
        for denom in ['0.25', '0.10', '0.05']:
            coin_value = float(denom)
            coins[denom] += int((amount // coin_value) if coin_value <= amount else 0)
        flash('Cannot withdraw the exact amount with available coins.')
    else:
        flash(f'Successfully withdrew ₱{amount:.2f} from {bank_name}.')

    return redirect(url_for('index'))

@app.route('/edit_bank_name', methods=['POST'])
def edit_bank_name():
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')
    if old_name in piggy_banks and new_name and new_name not in piggy_banks:
        piggy_banks[new_name] = piggy_banks.pop(old_name)
        flash(f"Bank name changed from '{old_name}' to '{new_name}'.")
    else:
        flash("Invalid or duplicate new name.")
    return redirect(url_for('index'))

@app.route('/transfer', methods=['POST'])
def transfer():
    from_bank = request.form.get('from_bank')
    to_bank = request.form.get('to_bank')
    try:
        amount = float(request.form.get('amount'))
    except (TypeError, ValueError):
        flash('Invalid transfer amount.')
        return redirect(url_for('index'))

    if (from_bank not in piggy_banks or to_bank not in piggy_banks or
        from_bank == to_bank or amount <= 0):
        flash('Invalid banks or amount.')
        return redirect(url_for('index'))

    # Get the transfer limit for the source bank
    transfer_limit = piggy_banks[from_bank].get('transfer_limit', 10.0)

    # Check transfer limit for today
    today = datetime.date.today()
    history = transfer_history.get(from_bank, {'date': today, 'amount': 0.0})
    if history['date'] != today:
        history = {'date': today, 'amount': 0.0}
    if history['amount'] + amount > transfer_limit:
        flash(f"Daily transfer limit (₱{transfer_limit:.2f}) exceeded for {from_bank}.")
        return redirect(url_for('index'))

    coins = piggy_banks[from_bank]
    total = coins['0.25']*0.25 + coins['0.10']*0.10 + coins['0.05']*0.05

    if amount > total:
        flash('Transfer amount exceeds current balance.')
        return redirect(url_for('index'))

    # Greedy algorithm to withdraw using largest coins first
    withdrawn = {'0.25': 0, '0.10': 0, '0.05': 0}
    remaining = round(amount, 2)
    for denom in ['0.25', '0.10', '0.05']:
        coin_value = float(denom)
        max_coins = min(coins[denom], int(remaining // coin_value))
        coins[denom] -= max_coins
        withdrawn[denom] = max_coins
        remaining -= round(max_coins * coin_value, 2)

    if abs(remaining) > 0.001:
        # Rollback
        for denom in ['0.25', '0.10', '0.05']:
            coins[denom] += withdrawn[denom]
        flash('Cannot transfer the exact amount with available coins.')
        return redirect(url_for('index'))

    # Add coins to target bank (using same denominations)
    for denom in ['0.25', '0.10', '0.05']:
        piggy_banks[to_bank][denom] += withdrawn[denom]

    # Update transfer history
    if today == history['date']:
        history['amount'] += amount
    transfer_history[from_bank] = history

    flash(f'Successfully transferred ₱{amount:.2f} from {from_bank} to {to_bank}.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)