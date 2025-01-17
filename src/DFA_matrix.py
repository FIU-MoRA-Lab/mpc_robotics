import random
import math
import otJC_precomputed as otJC
import secrets

MOORE_MACHINE_OUTPUT_BITS = 2 # need to make some assumption on this for garbled matrix element size

# p. 7 of Mohassel ODFA paper (Moore Variation)
def DfaMat(dfa, n):
    m = dfa['states']
    M = []
    for i in range(0, n + 1):
        row = []
        for j in range(0, m):
            res_0 = dfa['delta'][j][0]
            res_1 = dfa['delta'][j][1]
            output = dfa['outputs'][j]
            row.append((res_0, res_1, output))
        M.append(row)
    return M

# p. 7 of Mohassel ODFA paper (Moore Variation)
def singleMooreRow(dfa):
    m = dfa['states']
    row = []
    for j in range(0, m):
        res_0 = dfa['delta'][j][0]
        res_1 = dfa['delta'][j][1]
        output = dfa['outputs'][j]
        row.append((res_0, res_1, output))
    return row

# pretty print util
def print_M(M):
    for line in M:
        print(*line)

# M : DFA matrix
# n : number of bits in input string
# x : the input bit string
# q0 : initial state index
def evalDfa(M, n, x, q0):
    j = q0
    print('evaluating DFA matrix ...')
    for i in range(0, n):
        print('current output', M[i][j][2])
        j = M[i][j][int(x[i])]
    print('current output', M[n][j][2])
    return M[n][j][2]

# generate a matrix with n rows m cols, row elements are scrambled indices ranging [0, m).
def genPerm(n, m, k):
    Q = list(range(0, m))
    PER = []
    random.seed(secrets.randbits(k))
    for i in range(0, n):
        random.shuffle(Q)
        PER.append(Q[:])
    return PER

# Permute a DFA matrix M (with length n+1) with permutation matrix PER (with length n+2)
def permDfaMat(M, PER, n, q):
    PM = [[(-1, -1) for j in range(q)] for i in range(n)]
    for i in range(n):
        for j in range(q):
            j_permuted = PER[i][j] # pick a random index in this row of PM
            # make the i-th element of PM point to the same states in the next row as M[i][j] does.
            # These states will be placed at the PER[i + 1][M[i][j]]-th index of PM in the next iteration,
            # so point there with the promise that we will place them there next iteration.
            res_0 = PER[i + 1][M[i][j][0] ]
            res_1 = PER[i + 1][M[i][j][1] ]
            output = M[i][j][2]
            PM[i][j_permuted] = (res_0, res_1, output)
    return PM

# assume num2 is of n_digits digits. That is, 0b1 || 0b1 = 0b1 || 0b0001 = 0b10001 = 17 if n_digits = 4.
def numConcat(num1, num2, n_digits): 
     # add zeroes to the end of num1 
     num1 = num1 << n_digits
     # add num2 to num1 
     num1 += num2 
     return num1

def split_bits(n1_concat_n2, bits_n2):
    n1 = n1_concat_n2 >> bits_n2
    n2 = n1_concat_n2 ^ (n1 << bits_n2)
    return (n1, n2)

# return true if there are n zeros at the end of the given number.
def hasNTrailingZeros(number, n):
    return (number & (2**n - 1)) == 0 # AND bitmask with n-ones

class Alice:
    # Client encrypts her input at her current row_i and sends it to server in the form
    # (c_enc_a, c_prime_enc_a)
    def encrypt_input_i(self, round_num, n):
        self.r_d = otJC.alice_send_choices_enc(
            self.conn, 
            int(self.input[round_num*n + self.row_i]), 
            self.k_prime,
            self.s,
            self.ot_receiver_open_file
        )

    # used for getting the output at current state, without advancing to the next state yet.
    # we use this for revealing the output at the last row of the GM
    def revealColor(self, GM):
        random.seed(self.pad)
        # throw away first two pads
        for i in range(2):
            random.getrandbits(self.k_prime + self.s)
        pad = random.getrandbits(MOORE_MACHINE_OUTPUT_BITS)
        # print("ALICE:",len(GM))
        output = pad ^ GM[self.row_i][self.state][2]
        # if output != 2:
        #     print("Wrong color:", output)
        #     exit(1)
        # print("color", output)
        return output

    def resetRowI(self):
        self.row_i = 0

    # Client retrieves the keys and computes the final result.
    def step3(self, GM, round_num, n):
        # decrypt garbled key
        k_i = otJC.alice_compute_result(
            self.conn,
            int(self.input[round_num*n + self.row_i]), 
            self.r_d, 
            self.k_prime,
            self.s
        )

        # get the corresponding random nums
        random.seed(self.pad)
        pads = (
            random.getrandbits(self.k_prime + self.s), 
            random.getrandbits(self.k_prime + self.s)
        )
        # navigate to the next state (first guess)
        newstate_concat_newpad = k_i ^ pads[0] ^ GM[self.row_i][self.state][0]
        if not hasNTrailingZeros(newstate_concat_newpad, self.s):
            newstate_concat_newpad = k_i ^ pads[1] ^ GM[self.row_i][self.state][1]
            if not hasNTrailingZeros(newstate_concat_newpad, self.s):
                print("BAD Garbled Key or Pad! Neither element could be decrypted.")
        # strip zeros
        (newstate_concat_newpad, _) = split_bits(newstate_concat_newpad, self.s)
        (self.state, self.pad) = split_bits(newstate_concat_newpad, self.k)
        self.row_i += 1
        # color at the resulting state
        # print("ALICE STATE", self.state, "ROW_I", self.row_i)
        return self.revealColor(GM)

    def init_state_and_pad(self, init_state_index, init_pad):
        self.state = init_state_index
        self.pad = init_pad

    def __init__(self, conn, q, alice_input, k, s, ot_receiver_open_file):
        self.input = alice_input
        self.q = q
        self.k = k
        self.k_prime = self.k + math.ceil(math.log(self.q, 2))
        self.s = s
        self.state = None
        self.pad = None
        self.row_i = 0 # which row am I in?
        self.conn = conn
        self.ot_receiver_open_file = ot_receiver_open_file
        self.r_d = None

    # lags 1 round behind until the end
    def extend_input(self, alice_input, last_row):
        self.input += alice_input
        if last_row:
            # we need an extra input (can be meaningless) to get the output at the last state
            # this is because the garbled key for the last row must exist, even if it doesn't need to point to the correct delta.
            self.input += str(secrets.randbits(1))
    
    # def extend_GM(self, new_rows):
    #     self.GM.extend(new_rows)
		
class Bob:
    # Server mixes his inputs with client's and sends back to client in the form
    # (d_0_enc, d_1_enc). Alice tells us which row of the matrix she is currently looking at.
    def send_garbled_key(self, alice_i):
        strs = otJC.bob_send_strings_enc(
            self.conn,
            int(self.input[alice_i]), 
            self.K_enc[alice_i],
            self.k_prime,
            self.s,
            self.ot_sender_open_file
        )
        # if alice_i == 12:
        #     print(strs)

    def append_GM_row(self):
        new_gm_row = [(0,0,0)] * self.q
        # Server generates 1 random keypair for garbling:
        # (This is a cryptographically secure RNG, in the order of security bits)
        a = secrets.randbits(self.k_prime + self.s)
        b = secrets.randbits(self.k_prime + self.s)
        garbled_keypair = (a,b)
        # Server generates a new row to append to PAD:
        next_pad_row = [secrets.randbits(self.k) for i in range (self.q)]
        # server generates a new row to append to PER:
        next_per_row = genPerm(1, self.q, self.k)[0]
        # server generates a row to append to PM:
        new_pm_row = permDfaMat([self.m_row], [self.PER[len(self.PER) - 1], next_per_row], 1, self.q)[0]
        # Computing the Garbled DFA Matrix GMΓ from PMΓ
        for j in range (0, self.q):
            # could impliment a Mealy Machine with outputs on arcs of the DFA same way,
            # right now we just have the Moore Machine output copied twice
            # a = numConcat(new_pm_row[j][0], new_pm_row[j][2], MOORE_MACHINE_OUTPUT_BITS)
            a = numConcat(new_pm_row[j][0], next_pad_row[new_pm_row[j][0] ], self.k)
            a = numConcat(a, 0, self.s)
            # b = numConcat(new_pm_row[j][1], new_pm_row[j][2], MOORE_MACHINE_OUTPUT_BITS)
            b = numConcat(new_pm_row[j][1], next_pad_row[new_pm_row[j][1] ], self.k)
            b = numConcat(b, 0, self.s) 
            a = a ^ garbled_keypair[0]
            b = b ^ garbled_keypair[1]
            c = new_pm_row[j][2]
            new_gm_row[j] = (a,b,c)
            # Pseudo Random Number Generator G
            random.seed(self.PAD[len(self.PAD) - 1][j])
            a = random.getrandbits(self.k_prime + self.s)
            b = random.getrandbits(self.k_prime + self.s)
            c = random.getrandbits(MOORE_MACHINE_OUTPUT_BITS)
            pad = (a,b,c)
            a = new_gm_row[j][0] ^ pad[0]
            b = new_gm_row[j][1] ^ pad[1]
            c = new_gm_row[j][2] ^ pad[2]
            new_gm_row[j] = (a,b,c)

        self.M.append(self.m_row)
        self.PER.append(next_per_row)
        self.PAD.append(next_pad_row)
        self.PM.append(new_pm_row)
        self.GM.append(new_gm_row)
        self.K_enc.append(garbled_keypair)
        self.n += 1

    def extend_input(self, bob_input, last_row):
        self.input += bob_input
        if last_row:
            self.input += str(secrets.randbits(1))

    def __init__(self, conn, bob_input, dfa, k, s, ot_sender_open_file):
        self.input = bob_input
        self.dfa = dfa
        self.k = k
        self.s = s
        self.n = 0
        self.conn = conn
        self.ot_sender_open_file = ot_sender_open_file

        # start with 1 row of M, 1 row of PM, 1 row GM, 2 rows PER, 2 rows PAD, 1 garbled keypair
        self.q = dfa['states']
        self.k_prime = self.k + math.ceil(math.log(self.q, 2))
        new_gm_row = [(0,0,0)] * self.q
        # Server generates 1 random keypair for garbling:
        a = secrets.randbits(self.k_prime + self.s)
        b = secrets.randbits(self.k_prime + self.s)
        garbled_keypair = (a,b)
        self.m_row = singleMooreRow(self.dfa)
        # need to start with two rows for pad and permutation matrix
        # the best we can do is to start with cryptographically secure pad, for now.
        # later, we must use a cryptographically secure PRNG which supports a setseed operation.
        self.PAD = [[secrets.randbits(self.k) for j in range(self.q)] for i in range(2)]
        # print(self.PAD)
        self.PER = genPerm(2, self.q, self.k)
        self.PM = permDfaMat([self.m_row], self.PER, 1, self.q)
        for j in range (0, self.q):
            # could impliment a Mealy Machine with outputs on arcs of the DFA same way,
            # right now we just have the Moore Machine output copied twice
            # a = numConcat(self.PM[0][j][0], self.PM[0][j][2], MOORE_MACHINE_OUTPUT_BITS)
            a = numConcat(self.PM[0][j][0], self.PAD[1][self.PM[0][j][0] ], k)
            a = numConcat(a, 0, self.s)
            # b = numConcat(self.PM[0][j][1], self.PM[0][j][2], MOORE_MACHINE_OUTPUT_BITS)
            b = numConcat(self.PM[0][j][1], self.PAD[1][self.PM[0][j][1] ], k)
            b = numConcat(b, 0, self.s)
            a = a ^ garbled_keypair[0]
            b = b ^ garbled_keypair[1]
            c = self.PM[0][j][2]
            new_gm_row[j] = (a,b,c)
            # Pseudo Random Number Generator G
            random.seed(self.PAD[0][j])
            a = random.getrandbits(self.k_prime + self.s)
            b = random.getrandbits(self.k_prime + self.s)
            c = random.getrandbits(MOORE_MACHINE_OUTPUT_BITS)
            pad = (a,b,c)
            a = new_gm_row[j][0] ^ pad[0]
            b = new_gm_row[j][1] ^ pad[1]
            c = new_gm_row[j][2] ^ pad[2]
            new_gm_row[j] = (a,b,c)

        self.init_state = self.PER[0][dfa['initial'] ]
        self.init_pad = self.PAD[0][self.init_state]
        # print("BOB SENDS INIT STATE/PAD=", self.init_state, self.init_pad)
        self.conn.send((self.init_state, self.init_pad))

        self.M = [self.m_row]
        self.GM = [new_gm_row]
        self.K_enc = [garbled_keypair]