from behave import given, when, then
import base64
from algosdk import kmd
from algosdk import transaction
from algosdk import encoding
from algosdk import algod
from algosdk import account
from algosdk import mnemonic
from algosdk import wallet
from algosdk import auction
from algosdk import util
from algosdk import constants
from algosdk import template
import os
from datetime import datetime


@when("I create a wallet")
def create_wallet(context):
    context.wallet_name = "Walletpy"
    context.wallet_pswd = ""
    context.wallet_id = context.kcl.create_wallet(context.wallet_name, context.wallet_pswd)["id"]


@then("the wallet should exist")
def wallet_exist(context):
    wallets = context.kcl.list_wallets()
    wallet_names = [w["name"] for w in wallets]
    assert context.wallet_name in wallet_names


@when("I get the wallet handle")
def get_handle(context):
    context.handle = context.kcl.init_wallet_handle(context.wallet_id, context.wallet_pswd)


@then("I can get the master derivation key")
def get_mdk(context):
    mdk = context.kcl.export_master_derivation_key(context.handle, context.wallet_pswd)
    assert mdk


@when("I rename the wallet")
def rename_wallet(context):
    context.wallet_name = "Walletpy_new"
    context.kcl.rename_wallet(context.wallet_id, context.wallet_pswd, context.wallet_name)


@then("I can still get the wallet information with the same handle")
def get_wallet_info(context):
    info = context.kcl.get_wallet(context.handle)
    assert info


@when("I renew the wallet handle")
def renew_handle(context):
    if not hasattr(context, 'handle'):
        context.handle = context.kcl.init_wallet_handle(context.wallet_id, context.wallet_pswd)
    context.kcl.renew_wallet_handle(context.handle)


@when("I release the wallet handle")
def release_handle(context):
    context.kcl.release_wallet_handle(context.handle)


@then("the wallet handle should not work")
def try_handle(context):
    try:
        context.renew_wallet_handle(context.handle)
        context.error = False
    except:
        context.error = True
    assert context.error


@given('payment transaction parameters {fee} {fv} {lv} "{gh}" "{to}" "{close}" {amt} "{gen}" "{note}"')
def txn_params(context, fee, fv, lv, gh, to, close, amt, gen, note):
    context.fee = int(fee)
    context.fv = int(fv)
    context.lv = int(lv)
    context.gh = gh
    context.to = to
    context.amt = int(amt)
    if close == "none":
        context.close = None
    else:
        context.close = close
    if note == "none":
        context.note = None
    else:
        context.note = base64.b64decode(note)
    if gen == "none":
        context.gen = None
    else:
        context.gen = gen


@given('mnemonic for private key "{mn}"')
def mn_for_sk(context, mn):
    context.mn = mn
    context.sk = mnemonic.to_private_key(mn)
    context.pk = account.address_from_private_key(context.sk)


@when('I create the payment transaction')
def create_paytxn(context):
    context.txn = transaction.PaymentTxn(context.pk, context.fee, context.fv, context.lv, context.gh, context.to, context.amt, context.close, context.note, context.gen)


@given('multisig addresses "{addresses}"')
def msig_addresses(context, addresses):
    addresses = addresses.split(" ")
    context.msig = transaction.Multisig(1, 2, addresses)


@when("I create the multisig payment transaction")
def create_msigpaytxn(context):
    context.txn = transaction.PaymentTxn(context.msig.address(), context.fee, context.fv, context.lv, context.gh, context.to, context.amt, context.close, context.note, context.gen)
    context.mtx = transaction.MultisigTransaction(context.txn, context.msig)


@when("I sign the multisig transaction with the private key")
def sign_msig(context):
    context.mtx.sign(context.sk)


@when("I sign the transaction with the private key")
def sign_with_sk(context):
    context.stx = context.txn.sign(context.sk)


@then('the signed transaction should equal the golden "{golden}"')
def equal_golden(context, golden):
    assert encoding.msgpack_encode(context.stx) == golden


@then('the multisig address should equal the golden "{golden}"')
def equal_msigaddr_golden(context, golden):
    assert context.msig.address() == golden


@then('the multisig transaction should equal the golden "{golden}"')
def equal_msig_golden(context, golden):
    assert encoding.msgpack_encode(context.mtx) == golden


@when("I get versions with algod")
def acl_v(context):
    context.versions = context.acl.versions()["versions"]


@then("v1 should be in the versions")
def v1_in_versions(context):
    assert "v1" in context.versions


@when("I get versions with kmd")
def kcl_v(context):
    context.versions = context.kcl.versions()


@when("I get the status")
def status(context):
    context.status = context.acl.status()


@when("I get status after this block")
def status_block(context):
    context.status_after = context.acl.status_after_block(context.status["lastRound"])


@then("I can get the block info")
def block(context):
    context.block = context.acl.block_info(context.status["lastRound"]+1)


@when("I import the multisig")
def import_msig(context):
    context.wallet.import_multisig(context.msig)


@then("the multisig should be in the wallet")
def msig_in_wallet(context):
    msigs = context.wallet.list_multisig()
    assert context.msig.address() in msigs


@when("I export the multisig")
def exp_msig(context):
    context.exp = context.wallet.export_multisig(context.msig.address())


@then("the multisig should equal the exported multisig")
def msig_eq(context):
    assert encoding.msgpack_encode(context.msig) == encoding.msgpack_encode(context.exp)


@when("I delete the multisig")
def delete_msig(context):
    context.wallet.delete_multisig(context.msig.address())


@then("the multisig should not be in the wallet")
def msig_not_in_wallet(context):
    msigs = context.wallet.list_multisig()
    assert context.msig.address() not in msigs


@when("I generate a key using kmd")
def gen_key_kmd(context):
    context.pk = context.wallet.generate_key()


@then("the key should be in the wallet")
def key_in_wallet(context):
    keys = context.wallet.list_keys()
    assert context.pk in keys


@when("I delete the key")
def delete_key(context):
    context.wallet.delete_key(context.pk)


@then("the key should not be in the wallet")
def key_not_in_wallet(context):
    keys = context.wallet.list_keys()
    assert context.pk not in keys


@when("I generate a key")
def gen_key(context):
    context.sk, context.pk = account.generate_account()
    context.old = context.pk


@when("I import the key")
def import_key(context):
    context.wallet.import_key(context.sk)


@then("the private key should be equal to the exported private key")
def sk_eq_export(context):
    exp = context.wallet.export_key(context.pk)
    assert context.sk == exp
    context.wallet.delete_key(context.pk)


@given("a kmd client")
def kmd_client(context):
    data_dir_path = os.environ["NODE_DIR"] + "/"
    kmd_folder_name = os.environ["KMD_DIR"] + "/"
    kmd_token = open(data_dir_path + kmd_folder_name + "kmd.token",
                     "r").read().strip("\n")
    kmd_address = "http://" + open(data_dir_path + kmd_folder_name + "kmd.net",
                                   "r").read().strip("\n")
    context.kcl = kmd.KMDClient(kmd_token, kmd_address)


@given("an algod client")
def algod_client(context):
    data_dir_path = os.environ["NODE_DIR"] + "/"
    algod_token = open(data_dir_path + "algod.token", "r").read().strip("\n")
    algod_address = "http://" + open(data_dir_path + "algod.net",
                                     "r").read().strip("\n")
    context.acl = algod.AlgodClient(algod_token, algod_address)


@given("wallet information")
def wallet_info(context):
    context.wallet_name = "unencrypted-default-wallet"
    context.wallet_pswd = ""
    context.wallet = wallet.Wallet(context.wallet_name, context.wallet_pswd, context.kcl)
    context.wallet_id = context.wallet.id
    context.accounts = context.wallet.list_keys()


@given('default transaction with parameters {amt} "{note}"')
def default_txn(context, amt, note):
    params = context.acl.suggested_params()
    context.last_round = params["lastRound"]
    if note == "none":
        note = None
    else:
        note = base64.b64decode(note)
    context.txn = transaction.PaymentTxn(context.accounts[0], params["fee"], context.last_round, context.last_round+1000, params["genesishashb64"], context.accounts[1], int(amt), note=note, gen=params["genesisID"])
    context.pk = context.accounts[0]


@given('default multisig transaction with parameters {amt} "{note}"')
def default_msig_txn(context, amt, note):
    params = context.acl.suggested_params()
    context.last_round = params["lastRound"]
    if note == "none":
        note = None
    else:
        note = base64.b64decode(note)
    context.msig = transaction.Multisig(1, 1, context.accounts)
    context.txn = transaction.PaymentTxn(context.msig.address(), params["fee"], context.last_round, context.last_round + 1000, params["genesishashb64"], context.accounts[1], int(amt), note=note, gen=params["genesisID"])
    context.mtx = transaction.MultisigTransaction(context.txn, context.msig)
    context.pk = context.accounts[0]


@when("I get the private key")
def get_sk(context):
    context.sk = context.wallet.export_key(context.pk)


@when("I send the transaction")
def send_txn(context):
    try:
        context.acl.send_transaction(context.stx)
    except:
        context.error = True


@when("I send the kmd-signed transaction")
def send_txn_kmd(context):
    context.acl.send_transaction(context.stx_kmd)


@when("I send the bogus kmd-signed transaction")
def send_txn_kmd(context):
    try:
        context.acl.send_transaction(context.stx_kmd)
    except:
        context.error = True


@when("I send the multisig transaction")
def send_msig_txn(context):
    try:
        context.acl.send_transaction(context.mtx)
    except:
        context.error = True


@then("the transaction should go through")
def check_txn(context):
    last_round = context.acl.status()["lastRound"]
    assert "type" in context.acl.pending_transaction_info(context.txn.get_txid())
    context.acl.status_after_block(last_round+2)
    assert "type" in context.acl.transaction_info(context.txn.sender, context.txn.get_txid())
    assert "type" in context.acl.transaction_by_id(context.txn.get_txid())


@then("I can get the transaction by ID")
def get_txn_by_id(context):
    context.acl.status_after_block(context.last_round+2)
    assert "type" in context.acl.transaction_by_id(context.txn.get_txid())


@then("the transaction should not go through")
def txn_fail(context):
    assert context.error


@when("I sign the transaction with kmd")
def sign_kmd(context):
    context.stx_kmd = context.wallet.sign_transaction(context.txn)


@then("the signed transaction should equal the kmd signed transaction")
def sign_both_equal(context):
    assert encoding.msgpack_encode(context.stx) == encoding.msgpack_encode(context.stx_kmd)


@when("I sign the multisig transaction with kmd")
def sign_msig_kmd(context):
    context.mtx_kmd = context.wallet.sign_multisig_transaction(context.accounts[0], context.mtx)


@then("the multisig transaction should equal the kmd signed multisig transaction")
def sign_msig_both_equal(context):
    assert encoding.msgpack_encode(context.mtx) == encoding.msgpack_encode(context.mtx_kmd)


@when('I read a transaction "{txn}" from file "{num}"')
def read_txn(context, txn, num):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    context.num = num
    context.txn = transaction.retrieve_from_file(dir_path + "/temp/raw" + num + ".tx")[0]
    

@when("I write the transaction to file")
def write_txn(context):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    transaction.write_to_file([context.txn], dir_path + "/temp/raw" + context.num + ".tx")


@then("the transaction should still be the same")
def check_enc(context):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    new = transaction.retrieve_from_file(dir_path + "/temp/raw" + context.num + ".tx")
    old = transaction.retrieve_from_file(dir_path + "/temp/old" + context.num + ".tx")
    assert encoding.msgpack_encode(new[0]) == encoding.msgpack_encode(old[0])


@then("I do my part")
def check_save_txn(context):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.dirname(os.path.dirname(dir_path))
    stx = transaction.retrieve_from_file(dir_path + "/temp/txn.tx")[0]
    txid = stx.transaction.get_txid()
    last_round = context.acl.status()["lastRound"]
    context.acl.status_after_block(last_round + 2)
    assert context.acl.transaction_info(stx.transaction.sender, txid)


@then("I get the ledger supply")
def get_ledger(context):
    context.acl.ledger_supply()


@then("the node should be healthy")
def check_health(context):
    assert context.acl.health() == None


@when("I get the suggested params")
def suggested_params(context):
    context.params = context.acl.suggested_params()


@when("I get the suggested fee")
def suggested_params(context):
    context.fee = context.acl.suggested_fee()["fee"]


@then("the fee in the suggested params should equal the suggested fee")
def check_suggested(context):
    assert context.params["fee"] == context.fee


@when("I create a bid")
def create_bid(context):
    context.sk, pk = account.generate_account()
    context.bid = auction.Bid(pk, 1, 2, 3, pk, 4)


@when("I encode and decode the bid")
def enc_dec_bid(context):
    context.bid = encoding.msgpack_decode(encoding.msgpack_encode(context.bid))


@then("the bid should still be the same")
def check_bid(context):
    assert context.sbid == context.old


@when("I sign the bid")
def sign_bid(context):
    context.sbid = context.bid.sign(context.sk)
    context.old = context.bid.sign(context.sk)


@when("I decode the address")
def decode_addr(context):
    context.pk = encoding.decode_address(context.pk)


@when("I encode the address")
def encode_addr(context):
    context.pk = encoding.encode_address(context.pk)


@then("the address should still be the same")
def check_addr(context):
    assert context.pk == context.old


@when("I convert the private key back to a mnemonic")
def sk_to_mn(context):
    context.mn = mnemonic.from_private_key(context.sk)


@then('the mnemonic should still be the same as "{mn}"')
def check_mn(context, mn):
    assert context.mn == mn


@given('mnemonic for master derivation key "{mn}"')
def mn_for_mdk(context, mn):
    context.mn = mn
    context.mdk = mnemonic.to_master_derivation_key(mn)


@when("I convert the master derivation key back to a mnemonic")
def sk_to_mn(context):
    context.mn = mnemonic.from_master_derivation_key(context.mdk)


@when("I create the flat fee payment transaction")
def create_paytxn_flat_fee(context):
    context.txn = transaction.PaymentTxn(context.pk, context.fee, context.fv, context.lv, context.gh, context.to, context.amt, context.close, context.note, context.gen, flat_fee=True)


@given('encoded multisig transaction "{mtx}"')
def dec_mtx(context, mtx):
    context.mtx = encoding.msgpack_decode(mtx)


@when("I append a signature to the multisig transaction")
def append_mtx(context):
    context.mtx.sign(context.sk)


@given('encoded multisig transactions "{msigtxns}"')
def mtxs(context, msigtxns):
    context.mtxs = msigtxns.split(" ")
    context.mtxs = [encoding.msgpack_decode(m) for m in context.mtxs]


@when("I merge the multisig transactions")
def merge_mtxs(context):
    context.mtx = transaction.MultisigTransaction.merge(context.mtxs)


@when('I convert {microalgos} microalgos to algos and back')
def convert_algos(context, microalgos):
    context.microalgos = util.algos_to_microalgos(util.microalgos_to_algos(int(microalgos)))


@then("it should still be the same amount of microalgos {microalgos}")
def check_microalgos(context, microalgos):
    assert int(microalgos) == context.microalgos


@then("I get transactions by address and round")
def txns_by_addr_round(context):
    txns = context.acl.transactions_by_address(context.accounts[0], first=1, last=context.acl.status()["lastRound"])
    assert (txns == {} or "transactions" in txns)


@then("I get transactions by address only")
def txns_by_addr_only(context):
    txns = context.acl.transactions_by_address(context.accounts[0])
    assert (txns == {} or "transactions" in txns)


@then("I get transactions by address and date")
def txns_by_addr_date(context):
    date = datetime.today().strftime('%Y-%m-%d')
    txns = context.acl.transactions_by_address(context.accounts[0], from_date=date, to_date=date)
    assert (txns == {} or "transactions" in txns)


@then("I get pending transactions")
def txns_pending(context):
    txns = context.acl.pending_transactions()
    assert (txns == {} or "truncatedTxns" in txns)


@then("I get account information")
def acc_info(context):
    context.acl.account_info(context.accounts[0])


@then("I can get account information")
def new_acc_info(context):
    context.acl.account_info(context.pk)
    context.wallet.delete_key(context.pk)


@given('key registration transaction parameters {fee} {fv} {lv} "{gh}" "{votekey}" "{selkey}" {votefst} {votelst} {votekd} "{gen}" "{note}"')
def keyreg_txn_params(context, fee, fv, lv, gh, votekey, selkey, votefst, votelst, votekd, gen, note):
    context.fee = int(fee)
    context.fv = int(fv)
    context.lv = int(lv)
    context.gh = gh
    context.votekey = encoding.encode_address(base64.b64decode(votekey))
    context.selkey = encoding.encode_address(base64.b64decode(selkey))
    context.votefst = int(votefst)
    context.votelst = int(votelst)
    context.votekd = int(votekd)
    if note == "none":
        context.note = None
    else:
        context.note = base64.b64decode(note)
    if gen == "none":
        context.gen = None
    else:
        context.gen = gen


@when("I create the key registration transaction")
def create_keyreg_txn(context):
    context.txn = transaction.KeyregTxn(context.pk, context.fee, context.fv, context.lv, context.gh, context.votekey, 
                                        context.selkey, context.votefst, context.votelst, context.votekd, context.note, context.gen)


@when('I get recent transactions, limited by {cnt} transactions')
def step_impl(context, cnt):
    txns = context.acl.transactions_by_address(context.accounts[0], limit=int(cnt))
    assert (txns == {} or "transactions" in txns)


@given("default asset creation transaction with total issuance {total}")
def default_asset_creation_txn(context, total):
    context.total = int(total)
    params = context.acl.suggested_params()
    context.last_round = params["lastRound"]
    context.pk = context.accounts[0]
    asset_name = "asset"
    unit_name = "unit"
    context.txn = transaction.AssetConfigTxn(context.pk, 1, context.last_round, context.last_round + 100, params["genesishashb64"], total=context.total,
                        default_frozen=False, unit_name=unit_name, asset_name=asset_name, manager=context.pk, 
                        reserve=context.pk, freeze=context.pk, clawback=context.pk)

    context.expected_asset_info = {
        "defaultfrozen": False,
        "unitname": "unit",
        "assetname": "asset",
        "managerkey": context.pk,
        "reserveaddr": context.pk,
        "freezeaddr": context.pk,
        "clawbackaddr": context.pk,
        "creator": context.pk,
        "total": context.total,
        "decimals": 0,
        "metadatahash": None,
        "url": ""
    }


@given("default-frozen asset creation transaction with total issuance {total}")
def default_asset_creation_txn(context, total):
    context.total = int(total)
    params = context.acl.suggested_params()
    context.last_round = params["lastRound"]
    context.pk = context.accounts[0]
    asset_name = "asset"
    unit_name = "unit"
    context.txn = transaction.AssetConfigTxn(context.pk, 1, context.last_round, context.last_round + 100, params["genesishashb64"], total=context.total,
                        default_frozen=True, unit_name=unit_name, asset_name=asset_name, manager=context.pk, 
                        reserve=context.pk, freeze=context.pk, clawback=context.pk)

    context.expected_asset_info = {
        "defaultfrozen": False,
        "unitname": "unit",
        "assetname": "asset",
        "managerkey": context.pk,
        "reserveaddr": context.pk,
        "freezeaddr": context.pk,
        "clawbackaddr": context.pk,
        "creator": context.pk,
        "total": context.total,
        "decimals": 0,
        "metadatahash": None,
        "url": ""
    }

@Given("asset test fixture")
def asset_fixture(context):
    context.expected_asset_info = dict()
    context.rcv = context.accounts[1]


@When("I update the asset index")
def update_asset_index(context):
    assets = context.acl.list_assets()["assets"]
    indices = [a["AssetIndex"] for a in assets]
    context.asset_index = max(indices)


@When("I get the asset info")
def get_asset_info(context):
    context.asset_info = context.acl.asset_info(context.asset_index)


@Then("the asset info should match the expected asset info")
def asset_info_match(context):
    for k in context.expected_asset_info:
        assert (context.expected_asset_info[k] == context.asset_info.get(k)) or ((not context.expected_asset_info[k]) and (not context.asset_info.get(k)))


@When("I create an asset destroy transaction")
def create_asset_destroy_txn(context):
    lastRound = context.acl.status()["lastRound"]
    gh = context.acl.suggested_params()["genesishashb64"]
    context.txn = transaction.AssetConfigTxn(context.pk, 0, lastRound, lastRound+100, gh=gh , index=context.asset_index, strict_empty_address_check=False)


@Then("I should be unable to get the asset info")
def err_asset_info(context):
    err = False
    try:
        context.acl.asset_info(context.pk, context.asset_index)
    except:
        err = True
    assert err


@When("I create a no-managers asset reconfigure transaction")
def no_manager_txn(context):
    lastRound = context.acl.status()["lastRound"]
    gh = context.acl.suggested_params()["genesishashb64"]
    context.txn = transaction.AssetConfigTxn(context.pk, 0, lastRound, lastRound+100, gh=gh , index=context.asset_index, reserve=context.pk, clawback=context.pk, freeze=context.pk, strict_empty_address_check=False)

    context.expected_asset_info["managerkey"] = ""


@When("I create a transaction for a second account, signalling asset acceptance")
def accept_asset_txn(context):
    params = context.acl.suggested_params()
    last_round = params["lastRound"]
    gh = params["genesishashb64"]
    context.txn = transaction.AssetTransferTxn(context.rcv, 10, last_round, last_round+1000, gh, context.rcv, 0, context.asset_index)


@When("I create a transaction transferring {amount} assets from creator to a second account")
def transfer_assets(context, amount):
    params = context.acl.suggested_params()
    last_round = params["lastRound"]
    gh = params["genesishashb64"]
    context.txn = transaction.AssetTransferTxn(context.pk, 10, last_round, last_round+1000, gh, context.rcv, int(amount), context.asset_index)


@When("I create a transaction transferring {amount} assets from a second account to creator")
def transfer_assets(context, amount):
    params = context.acl.suggested_params()
    last_round = params["lastRound"]
    gh = params["genesishashb64"]
    context.txn = transaction.AssetTransferTxn(context.rcv, 10, last_round, last_round+1000, gh, context.pk, int(amount), context.asset_index)


@Then("the creator should have {exp_balance} assets remaining")
def check_asset_balance(context, exp_balance):
    asset_info = context.acl.account_info(context.pk)["assets"][str(context.asset_index)]
    assert asset_info["amount"] == int(exp_balance)


@When("I create a freeze transaction targeting the second account")
def freeze_txn(context):
    params = context.acl.suggested_params()
    last_round = params["lastRound"]
    gh = params["genesishashb64"]
    context.txn = transaction.AssetFreezeTxn(context.pk, 10, last_round, last_round+1000, gh, context.asset_index, context.rcv, True)


@When("I create an un-freeze transaction targeting the second account")
def freeze_txn(context):
    params = context.acl.suggested_params()
    last_round = params["lastRound"]
    gh = params["genesishashb64"]
    context.txn = transaction.AssetFreezeTxn(context.pk, 10, last_round, last_round+1000, gh, context.asset_index, context.rcv, False)


@when("I create a transaction revoking {amount} assets from a second account to creator")
def revoke_txn(context, amount):
    params = context.acl.suggested_params()
    last_round = params["lastRound"]
    gh = params["genesishashb64"]
    context.txn = transaction.AssetTransferTxn(context.pk, 10, last_round, last_round+1000, gh, context.pk, int(amount), context.asset_index, revocation_target=context.rcv)


@given("a split contract with ratio {ratn} to {ratd} and minimum payment {min_pay}")
def split_contract(context, ratn, ratd, min_pay):
    context.params = context.acl.suggested_params()
    context.template = template.Split(context.accounts[0], context.accounts[1], context.accounts[2], ratn, ratd, context.params["lastRound"]+1000, min_pay, 2000)


@when("I send the split transactions")
def send_split(context):
    txns = context.template.get_send_funds_transactions(1234, context.params["lastRound"], context.params["lastRound"]+1000, context.params["genesishashb64"], False)
    context.txn = txns[0]
    context.acl.send_transactions(txns)


@given('an HTLC contract with preimage "{preimage}"')
def htlc_contract(context, preimage):
    context.params = context.acl.suggested_params()
    # hash the preimage here and insert
    context.template = template.HTLC(context.accounts[0], context.accounts[1], "sha256", "hash here", context.params["lastRound"]+1000, 2000)
    context.contract_account = context.template.get_address()


@when("I fund the contract account")
def fund_contract(context):
    context.txn = transaction.PaymentTxn(context.accounts[0], 0, context.params["lastRound"], context.params["lastRound"]+1000, context.params["genesishashb64"], context.contract_account, 1000000)
    context.acl.send_transaction(context.txn)


@when("I claim the algos")
def claim_algos(context):
    pass


@given("a periodic payment contract with withdrawing window {wd_window} and period {period}")
def periodic_pay_contract(context, wd_window, period):
    context.params = context.acl.suggested_params()
    context.template = template.PeriodicPayment(context.accounts[1], 12345, wd_window,
                                                period, 2000, context.params["lastRound"]+1000)
    context.contract_account = context.template.get_address()


@when("I claim the periodic payment")
def claim_periodic(context):
    context.txn = context.template.get_withdrawal_transaction(context.params["lastRound"], context.params["genesishashb64"], 0)
    context.acl.send_transaction(context.txn)


@given("a limit order contract with parameters {ratn} {ratd} {min_trade}")
def limit_order_contract(context, ratn, ratd, min_trade):
    context.params = context.acl.suggested_params()
    context.template = template.LimitOrder(context.accounts[0], context.asset_id, ratn, ratd, context.params["lastRound"]+1000, 2000, min_trade)
    context.contract_account = context.template.get_address()
    context.sk = context.kcl.export_key(context.accounts[1])


@when("I swap assets for algos")
def swap_assets(context):
    context.txns = context.template.get_swap_assets_transactions(12345, context.template.get_program(), context.sk, context.params["lastRound"], context.params["lastRound"]+1000, context.params["genesishashb64"], 0)
    context.acl.send_transactions(context.txns)


@given("a dynamic fee contract with amount {amt}")
def dynamic_fee_contract(context, amt):
    context.params = context.acl.suggested_params()
    context.sk = context.kcl.export_key(context.accounts[0])
    context.template = template.DynamicFee(context.accounts[1], 12345, context.params["lastRound"], context.params["lastRound"]+1000)
    context.contract_account = context.template.get_address()
    txn, lsig = context.template.sign_dynamic_fee(context.sk, context.params["genesishashb64"])
    context.txns = context.template.get_transactions(txn, lsig, context.kcl.export_key(context.accounts[2]), 0, context.params["lastRound"], context.params["lastRound"]+1000)

@when("I send the dynamic fee transactions")
def send_dynamic_fee(context):
    context.acl.send_transactions(context.txns)


