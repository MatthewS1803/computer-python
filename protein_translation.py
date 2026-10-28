codon_pairs = {
    'AUG': 'Methionine',
    'UUU' : 'Phenylalanine',
    'UUC' : 'Phenylalanine',
    'UUA': 'Leucine',
    'UUG' : 'Leucine',
    'UCU' : 'Serine',
    'UCC' : 'Serine',
    'UCA' : 'Serine',
    'UCG' : 'Serine',
    'UAU' : 'Tyrosine',
    'UAC' : 'Tyrosine',
    'UGU' : 'Cysteine',
    'UGC' : 'Cysteine',
    'UGG' : 'Tryptophan',
    'UAA' : 'STOP',
    'UAG' : 'STOP',
    'UGA' : 'STOP'
}

def proteins(strand):
    result = []
    for i in range(0, len(strand), 3):
        codon = strand[i:i + 3]
        if codon not in codon_pairs:
            raise ValueError('codon does not exist')
        else:
            if codon_pairs[codon] == 'STOP':
                break
            else:
                amino_acid = codon_pairs[codon]
                result.append(amino_acid)

    return result

    

print(proteins('UUAUUG'))