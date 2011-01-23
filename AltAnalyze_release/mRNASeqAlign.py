###mRNASeqAlign
#Copyright 2005-2008 J. David Gladstone Institutes, San Francisco California
#Author Nathan Salomonis - nsalomonis@gmail.com

#Permission is hereby granted, free of charge, to any person obtaining a copy 
#of this software and associated documentation files (the "Software"), to deal 
#in the Software without restriction, including without limitation the rights 
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
#copies of the Software, and to permit persons to whom the Software is furnished 
#to do so, subject to the following conditions:

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
#INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
#PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
#OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
#SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys, string
import os.path
import unique
import statistics
import copy
import time
import export; reload(export)

################# General File Parsing Functions #################

def filepath(filename):
    fn = unique.filepath(filename)
    return fn

def read_directory(sub_dir):
    dir_list = unique.read_directory(sub_dir); dir_list2 = [] 
    for entry in dir_list:
        if entry[-4:] == ".txt" or entry[-4:] == ".all" or entry[-5:] == ".data" or entry[-3:] == ".fa": dir_list2.append(entry)
    return dir_list2

class GrabFiles:
    def setdirectory(self,value): self.data = value
    def display(self): print self.data
    def searchdirectory(self,search_term):
        #self is an instance while self.data is the value of the instance
        files = getDirectoryFiles(self.data,str(search_term))
        if len(files)<1: print search_term,'not found'
        return files
    def returndirectory(self):
        dir_list = getAllDirectoryFiles(self.data)
        return dir_list

def getAllDirectoryFiles(import_dir):
    all_files = []
    dir_list = read_directory(import_dir)  #send a sub_directory to a function to identify all files in a directory
    for data in dir_list:    #loop through each file in the directory to output results
        data_dir = import_dir[1:]+'/'+data
        all_files.append(data_dir)
    return all_files

def getDirectoryFiles(import_dir, search_term):
    dir_list = read_directory(import_dir)  #send a sub_directory to a function to identify all files in a directory
    matches=[]
    for data in dir_list:    #loop through each file in the directory to output results
        data_dir = import_dir[1:]+'/'+data
        if search_term in data_dir: matches.append(data_dir)
    return matches

################# General Use Functions #################

def cleanUpLine(line):
    line = string.replace(line,'\n','')
    line = string.replace(line,'\c','')
    data = string.replace(line,'\r','')
    data = string.replace(data,'"','')
    return data

def combineDBs(db1,db2):
    for i in db2:
        try: db1[i]+=db2[i]
        except KeyError: db1[i]=db2[i]
    return db1

def eliminateRedundant(database):
    db1={}
    for key in database:
        list = unique.unique(database[key])
        list.sort()
        db1[key] = list
    return db1

################# Sequence Parsing and Comparison #################

def simpleSeqMatchProtocol(probeset_seq_data,mRNA_seq):
    """ Since it is possible for a probeset to be analyzed more than once for junction arrays
    (see probeset_seq_data junction design), only analyze a probeset once."""
    
    results=[]; probesets_analyzed = {}
    for y in probeset_seq_data:
        try: exon_seq = y.ExonSeq(); probeset = y.Probeset()
        except AttributeError: probeset = y.Probeset(); print [probeset],'seq missing';kill
        """if probeset == 'G7203664@J946608_RC@j_at':
            print exon_seq
            print mRNA_seq;kill"""
        if probeset not in probesets_analyzed:
            if exon_seq in mRNA_seq: call=1
            elif array_type == 'exon':
                if exon_seq[:25] in mRNA_seq: call=1
                elif exon_seq[-25:] in mRNA_seq: call=1
                else: call = 0
            else: call = 0
            #else: junction_seq = y.JunctionSeq()
            results.append((call,probeset))
            probesets_analyzed[probeset]=[]
    return results

def importEnsemblTranscriptSequence(Species,Array_type,probeset_seq_db):
    global species; global array_type
    species = Species; array_type = Array_type
    start_time = time.time()

    import_dir = '/AltDatabase/'+species+'/SequenceData' ### Multi-species file
    g = GrabFiles(); g.setdirectory(import_dir)
    seq_files = g.searchdirectory('cdna.all'); seq_files.sort(); filename = seq_files[-1]
    
    output_file = 'AltDatabase/'+species+'/SequenceData/output/'+array_type+'_Ens-mRNA_alignments.txt'
    dataw = export.ExportFile(output_file)  
    
    output_file = 'AltDatabase/'+species+'/SequenceData/output/sequences/'+array_type+'_Ens_mRNA_seqmatches.txt'
    datar = export.ExportFile(output_file)
    
    print "Begining generic fasta import of",filename
    fn=filepath(filename); sequence = ''; x = 0; count = 0; global gene_not_found; gene_not_found=[]; genes_found={}
    for line in open(fn,'rU').xreadlines():
        exon_start=1; exon_stop=1
        try: data, newline= string.split(line,'\n')
        except ValueError: continue
        try:
            if data[0] == '>':
                    if len(sequence) > 0:
                        gene_found = 'no'
                        if ensembl_id in probeset_seq_db:
                            genes_found[ensembl_id]=[]; seq_type = 'full-length'
                            probeset_seq_data = probeset_seq_db[ensembl_id]; cDNA_seq = sequence[1:]; mRNA_length = len(cDNA_seq)
                            results = simpleSeqMatchProtocol(probeset_seq_data,cDNA_seq)
                            for (call,probeset) in results:
                                dataw.write(string.join([probeset,str(call),transid],'\t')+'\n')
                            ###Save all sequences to the disk rather than store these in memory. Just select the optimal sequences later. 
                            values = [transid,cDNA_seq]
                            values = string.join(values,'\t')+'\n'; datar.write(values); x+=1
                        else: gene_not_found.append(ensembl_id)
                    t= string.split(data[1:],':'); sequence=''
                    transid_data = string.split(t[0],' '); transid = transid_data[0]; ensembl_id = t[-1]
        except IndexError: continue
        try:
            if data[0] != '>': sequence = sequence + data
        except IndexError:  continue
    datar.close(); dataw.close()
    end_time = time.time(); time_diff = int(end_time-start_time)
    gene_not_found = unique.unique(gene_not_found)
    print len(genes_found), 'genes associated with Ensembl transcripts'
    print len(gene_not_found), "genes not found in the reciprocol junction database (should be there unless conflict present - or few alternative genes predicted during junction array design)"
    print gene_not_found[0:10],'not found examples'
    print "Ensembl transcript sequences analyzed in %d seconds" % time_diff
    
def importUCSCTranscriptSequences(species,array_type,probeset_seq_db):
    start_time = time.time()

    if force == 'yes':
        ### Download mRNA sequence file from website
        import UI; import update
        file_location_defaults = UI.importDefaultFileLocations()
        fld = file_location_defaults['UCSCseq']
        for fl in fld:
            if species in fl.Species(): ucsc_default_dir = fl.Location()
        ucsc_mRNA_dir = ucsc_default_dir+'mrna.fa.gz'
        output_dir = 'AltDatabase/'+species+'/SequenceData/'
        gz_filepath, status = update.download(ucsc_mRNA_dir,output_dir,'')        
        if status == 'not-removed':
            try: os.remove(gz_filepath) ### Not sure why this works now and not before
            except OSError: status = status
            
    filename = 'AltDatabase/'+species+'/SequenceData/mrna.fa'
    output_file = 'AltDatabase/'+species+'/SequenceData/output/'+array_type+'_UCSC-mRNA_alignments.txt'
    dataw = export.ExportFile(output_file)      
    output_file = 'AltDatabase/'+species+'/SequenceData/output/sequences/'+array_type+'_UCSC_mRNA_seqmatches.txt'
    datar = export.ExportFile(output_file)

    ucsc_mrna_to_gene = importUCSCTranscriptAssociations(species)    
    
    print "Begining generic fasta import of",filename
    #'>gnl|ENS|Mm#S10859962 Mus musculus 12 days embryo spinal ganglion cDNA /gb=AK051143 /gi=26094349 /ens=Mm.1 /len=2289']
    #'ATCGTGGTGTGCCCAGCTCTTCCAAGGACTGCTGCGCTTCGGGGCCCAGGTGAGTCCCGC'
    fn=filepath(filename); sequence = '|'; ucsc_mRNA_hit_len={}; ucsc_probeset_null_hits={}; k=0
    fn=filepath(filename); sequence = '|'; ucsc_mRNA_hit_len={}; ucsc_probeset_null_hits={}; k=0
    for line in open(fn,'rU').xreadlines():
        try: data, newline= string.split(line,'\n')
        except ValueError: continue
        if len(data)>0:
            if data[0] != '#':
                try:
                    if data[0] == '>':
                        if len(sequence) > 1:
                            if accession in ucsc_mrna_to_gene:
                                gene_found = 'no'
                                for ens_gene in ucsc_mrna_to_gene[accession]:
                                    if ens_gene in probeset_seq_db:
                                        sequence = string.upper(sequence); gene_found = 'yes'
                                        mRNA_seq = sequence[1:]; mRNA_length = len(mRNA_seq)    
                                        k+=1; probeset_seq_data = probeset_seq_db[ens_gene]
                                        results = simpleSeqMatchProtocol(probeset_seq_data,mRNA_seq)
                                        for (call,probeset) in results:
                                            dataw.write(string.join([probeset,str(call),accession],'\t')+'\n')
                                if gene_found == 'yes':
                                    values = [accession,mRNA_seq]; values = string.join(values,'\t')+'\n'
                                    datar.write(values)
                        values = string.split(data,' '); accession = values[0][1:]
                        sequence = '|'; continue
                except IndexError: null = []       
                try:
                    if data[0] != '>': sequence = sequence + data
                except IndexError: print kill; continue
    datar.close()
    end_time = time.time(); time_diff = int(end_time-start_time)
    print "UCSC mRNA sequences analyzed in %d seconds" % time_diff

def importUCSCTranscriptAssociations(species):
    ### Import GenBank ACs that are redundant with Ensembl ACs
    filename = 'AltDatabase/ucsc/'+species+'/'+species+'_UCSC-accession-eliminated_mrna.txt'
    fn=filepath(filename); remove={}
    for line in open(fn,'rU').readlines():
        mRNA_ac = cleanUpLine(line)
        remove[mRNA_ac] = []

    ###This function is used to extract out EnsExon to EnsTranscript relationships to find out directly
    ###which probesets associate with which transcripts and then which proteins
    filename = 'AltDatabase/ucsc/'+species+'/'+species+'_UCSC-accession-to-gene_mrna.txt'
    fn=filepath(filename); ucsc_mrna_to_gene={}
    for line in open(fn,'rU').readlines():
        data = cleanUpLine(line)
        t = string.split(data,'\t')
        mRNA_ac, ens_genes, num_ens_exons = t
        #if mRNA_ac not in accession_index: ###only add mRNAs not examined in UniGene
        ens_genes = string.split(ens_genes,'|')
        if mRNA_ac not in remove: ucsc_mrna_to_gene[mRNA_ac] = ens_genes

        
    return ucsc_mrna_to_gene

################# Import Exon/Junction Data #################

class SplicingAnnotationData:
    def ArrayType(self):
        self._array_type = array_type
        return self._array_type
    def Probeset(self): return self._probeset
    def GeneID(self): return self._geneid
    def SetExonSeq(self,seq): self._exon_seq = seq
    def ExonSeq(self): return string.upper(self._exon_seq)
    def SetJunctionSeq(self,seq): self._junction_seq = seq
    def JunctionSeq(self): return string.upper(self._junction_seq)
    def RecipricolProbesets(self): return self._junction_probesets
    def Report(self):
        output = self.Probeset() +'|'+ self.ExternalGeneID()
        return output
    def __repr__(self): return self.Report()

class AffyExonSTDataSimple(SplicingAnnotationData):
    def __init__(self,probeset_id,ensembl_gene_id,exon_id,ens_exon_ids):
        self._geneid = ensembl_gene_id; self._external_gene = ensembl_gene_id; self._exonid = exon_id
        self._external_exonids = ens_exon_ids; self._probeset=probeset_id

class JunctionDataSimple(SplicingAnnotationData):
    def __init__(self,probeset_id,array_geneid):
        self._probeset=probeset_id; self._external_gene = array_geneid
    
def importSplicingAnnotationDatabase(filename):
    global exon_db; fn=filepath(filename)
    print 'importing', filename
    exon_db={}; count = 0; x = 0
    for line in open(fn,'rU').readlines():             
        probeset_data,null = string.split(line,'\n')  #remove endline
        if x == 0: x = 1
        else:
            t = string.split(probeset_data,'\t'); probeset_id = t[0]; probeset_id = t[2]
            probe_data = AffyExonSTDataSimple(probeset_id,ensembl_gene_id)
            exon_db[probeset_id] = probe_data
    return exon_db

def importProbesetSequences(exon_db,species):
    ### First import the probeset sequence file
    import_dir = '/AltDatabase'+'/'+species+'/SequenceData'
    try: dir_list = read_directory(import_dir)  #send a sub_directory to a function to identify all files in a directory
    except Exception:
        ### create directory for file to download
        export.createExportFolder(import_dir[1:])
        ### Download the data from the AltAnalyze website
        import update
        probeset_seq_file = 'DEFINEME'
        update.downloadCurrentVersion(probeset_seq_file,species,'')
        dir_list = read_directory(import_dir)
    for input_file in dir_list:    #loop through each file in the directory to output results
        if '.probeset.fa' in input_file: filename = import_dir[1:]+'/'+input_file
        else: print 'probeset sequence file not found';kill
        
    print 'importing', filename; probeset_seq_db={}; probesets_parsed=0; probesets_added=0
    chromosome = 'chr'+str(chromosome)
    print "Begining generic fasta import of",filename
    fn=filepath(filename); sequence = ''; x = 0;count = 0
    for line in open(fn,'rU').xreadlines():
        try: data, newline= string.split(line,'\n')
        except ValueError: continue
        try:
            if data[0] == '>':
                    try: 
                        try:
                            y = exon_db[probeset]; sequence = string.upper(sequence)
                            gene = y.GeneID(); y.SetExonSeq(sequence)
                            try: probeset_seq_db[gene].append(y)
                            except KeyError: probeset_seq_db[gene] = [y]
                            sequence = ''; t= string.split(data,';'); probesets_added+=1
                            probeset=t[0]; probeset_data = string.split(probeset,':'); probeset = probeset_data[-1]
                            chr = t[2]; chr = string.split(chr,'='); chr = chr[-1]; probesets_parsed +=1
                        except KeyError:
                            sequence = ''; t= string.split(data,';')
                            probeset=t[0]; probeset_data = string.split(probeset,':'); probeset = probeset_data[-1]
                            chr = t[2]; chr = string.split(chr,'='); chr = chr[-1]; probesets_parsed +=1
                    except UnboundLocalError: ###Occurs for the first entry
                        t= string.split(data,';'); probeset=t[0]; probeset_data = string.split(probeset,':'); probeset = probeset_data[-1]
                        chr = t[2]; chr = string.split(chr,'='); chr = chr[-1]; probesets_parsed +=1
            else: sequence = sequence + data
        except IndexError: continue
        
    y = exon_db[probeset]; sequence = string.upper(sequence)
    gene = y.GeneID(); y.SetExonSeq(sequence)
    try: probeset_seq_db[gene].append(y)
    except KeyError: probeset_seq_db[gene] = [y]

    print len(probeset_seq_db), probesets_added, probesets_parsed, len(exon_db)
    return probeset_seq_db

def importJunctionAnnotationDatabaseAndSequence(species,array_type,biotype):
    """This function imports AffyGene-Ensembl relationships, junction probeset sequences, and recipricol junction comparisons.
    with data stored from this function, we can match probeset sequence to mRNAs and determine which combinations of probesets
    can be used as match-match or match-nulls."""

    array_ens_db={}
    if array_type == 'AltMouse':
        ### Import AffyGene to Ensembl associations (e.g., AltMouse array)    
        filename = 'AltDatabase/'+species+'/'+array_type+'/'+array_type+'-Ensembl_relationships.txt'
        fn=filepath(filename); x = 0
        for line in open(fn,'rU').xreadlines():
            data, newline = string.split(line,'\n'); t = string.split(data,'\t')
            if x==0: x=1
            else: 
                array_gene,ens_gene = t
                try: array_ens_db[array_gene].append(ens_gene)
                except KeyError: array_ens_db[array_gene]=[ens_gene]

    filename = 'AltDatabase/'+species+'/'+array_type+'/'+array_type+'_critical-junction-seq.txt'  
    try: probeset_seq_db = importCriticalJunctionSeq(filename,species,array_type)
    except IOError:
        import update
        update.downloadCurrentVersion(filename,array_type,'txt')
        probeset_seq_db = importCriticalJunctionSeq(filename,species,array_type)
    
    ###Import reciprocol junctions, so we can compare these directly instead of hits to nulls and combine with sequence data
    ###This short-cuts what we did in two function in ExonModule with exon level data
    if array_type == 'AltMouse': filename = 'AltDatabase/'+species+'/'+array_type+'/'+array_type+'_junction-comparisons.txt'
    elif array_type == 'junction': filename = 'AltDatabase/'+species+'/'+array_type+'/'+species+'_junction_comps_updated.txt'
    elif array_type == 'RNASeq': filename = 'AltDatabase/'+species+'/'+array_type+'/'+species+'_junction_comps.txt'
    fn=filepath(filename); probeset_gene_seq_db={}; added_probesets={}; pairwise_probesets={}; x = 0
    for line in open(fn,'rU').xreadlines():
        data, newline = string.split(line,'\n'); t = string.split(data,'\t')
        if x==0: x=1
        else:
            if (array_type == 'junction' or array_type == 'RNASeq'):
                array_gene, critical_exons,excl_junction,incl_junction, probeset2, probeset1, data_source = t
                array_ens_db[array_gene]=[array_gene]
            elif array_type == 'AltMouse':
                array_gene,probeset1,probeset2,critical_exons = t #; critical_exons = string.split(critical_exons,'|')
            probesets = [probeset1,probeset2]
            pairwise_probesets[probeset1,probeset2] = []
            if array_gene in array_ens_db:
                ensembl_gene_ids = array_ens_db[array_gene]
                for probeset_id in probesets:
                    if probeset_id in probeset_seq_db:
                        probeset_seq,junction_seq = probeset_seq_db[probeset_id]
                        if biotype == 'gene':
                            for ensembl_gene_id in ensembl_gene_ids:
                                if probeset_id not in added_probesets:
                                    probe_data = JunctionDataSimple(probeset_id,array_gene)
                                    probe_data.SetExonSeq(probeset_seq)
                                    probe_data.SetJunctionSeq(junction_seq)
                                    try: probeset_gene_seq_db[ensembl_gene_id].append(probe_data)
                                    except KeyError: probeset_gene_seq_db[ensembl_gene_id] = [probe_data]
                                    added_probesets[probeset_id]=[]
    print len(probeset_gene_seq_db),"genes with probeset sequence associated"
    return probeset_gene_seq_db,pairwise_probesets

################# Import Sequence Match Results and Re-Output #################

def importCriticalJunctionSeq(filename,species,array_type):       
    fn=filepath(filename); probeset_seq_db={}; x = 0
    for line in open(fn,'rU').xreadlines():
        data, newline = string.split(line,'\n'); t = string.split(data,'\t')
        if x==0: x=1
        else: 
            try: probeset,probeset_seq,junction_seq = t
            except Exception: probeset,probeset_seq,junction_seq, null = t
            probeset_seq=string.replace(probeset_seq,'|','')
            probeset_seq_db[probeset] = probeset_seq,junction_seq
            x+=1
            
    print len(probeset_seq_db),'probesets with associated sequence'
    return probeset_seq_db

def reAnalyzeRNAProbesetMatches(align_files,species,array_type,pairwise_probeset_combinations):
    """Import matching and non-matching probesets and export the valid comparisons"""
    align_files2=[]
    for file in align_files:
        if array_type in file: align_files2.append(file)
    align_files = align_files2
    
    matching={}; not_matching={}
    for filename in align_files:
        print 'Reading',filename
        start_time = time.time()
        fn=filepath(filename)
        for line in open(fn,'rU').xreadlines():
            values = string.replace(line,'\n','')
            probeset,call,accession = string.split(values,'\t')
            if call == '1':
                try: matching[probeset].append(accession)
                except KeyError: matching[probeset] = [accession]
            else:
                try: not_matching[probeset].append(accession)
                except KeyError: not_matching[probeset] = [accession]

    probeset_matching_pairs={}; matching_in_both=0; match_and_null=0; no_matches=0; no_nulls=0
    for (probeset1,probeset2) in pairwise_probeset_combinations:                
        if probeset1 in matching and probeset2 in matching:
            matching[probeset1].sort(); matching[probeset2].sort()
            match1 = string.join(matching[probeset1],'|')
            match2 = string.join(matching[probeset2],'|')
            if match1 != match2:
                probeset_matching_pairs[probeset1+'|'+probeset2] = [match1,match2]
            matching_in_both+=1
        else:
            if probeset1 in matching and probeset1 in not_matching:
                match = string.join(matching[probeset1],'|')
                null_match = string.join(not_matching[probeset1],'|')
                probeset_matching_pairs[probeset1] = [match,null_match]
                match_and_null+=1
            elif probeset2 in matching and probeset2 in not_matching:
                match = string.join(matching[probeset2],'|')
                null_match = string.join(not_matching[probeset2],'|')
                probeset_matching_pairs[probeset2] = [match,null_match]
                match_and_null+=1
            elif probeset1 in matching or probeset2 in matching: no_nulls+=1
            else:
                no_matches+=1
                #if no_matches<10: print probeset1,probeset2

    print matching_in_both, "probeset pairs with matching isoforms for both recipricol probesets."
    print match_and_null, "probeset pairs with a match for one and null for that one."
    print no_nulls, "probeset pairs with only one match."
    print no_matches, "probeset pairs with no matches."
    
    import IdentifyAltIsoforms
    export_file = 'AltDatabase/'+species+'/'+array_type+'/'+species+'_all-transcript-matches.txt'     
    IdentifyAltIsoforms.exportSimple(probeset_matching_pairs,export_file,'')

################# Main Run Options #################
    
def alignProbesetsToTranscripts(species,array_type,Force):
    global force; force = Force
    """Match exon or junction probeset sequences to Ensembl and USCS mRNA transcripts"""
      
    if array_type == 'AltMouse' or array_type == 'junction' or array_type == 'RNASeq':
        data_type = 'junctions'; probeset_seq_file=''
        if data_type == 'junctions':
            start_time = time.time(); biotype = 'gene' ### Indicates whether to store information at the level of genes or probesets
            probeset_seq_db,pairwise_probeset_combinations = importJunctionAnnotationDatabaseAndSequence(species,array_type,biotype)
            end_time = time.time(); time_diff = int(end_time-start_time)
        elif data_type == 'critical-exons':
            ### NOTE: Below code not tested
            probeset_annotations_file = "AltDatabase/"+species+"/"+array_type+'/'+species+"_Ensembl_"+array_type+"_probesets.txt"
            ###Import probe-level associations
            exon_db = importSplicingAnnotationDatabase(probeset_annotations_file)
            start_time = time.time()
            probeset_seq_db = importProbesetSequences(exon_db,species)  ###Do this locally with a function that works on tab-delimited as opposed to fasta sequences (exon array)
            end_time = time.time(); time_diff = int(end_time-start_time)
        print "Analyses finished in %d seconds" % time_diff
    elif array_type == 'exon':
        data_type = 'exon'
        probeset_annotations_file = 'AltDatabase/'+species+'/'+array_type+'/'+species+'_Ensembl_probesets.txt'
        ###Import probe-level associations
        exon_db = importSplicingAnnotationDatabase(probeset_annotations_file)
        start_time = time.time()
        probeset_seq_db = importProbesetSequences(exon_db,species)
        end_time = time.time(); time_diff = int(end_time-start_time)
        print "Analyses finished in %d seconds" % time_diff

    ### Match probesets to mRNAs
    importEnsemblTranscriptSequence(species,array_type,probeset_seq_db)
    importUCSCTranscriptSequences(species,array_type,probeset_seq_db)

    probeset_seq_db={} ### Re-set db

    ### Import results if junction array to make comparisons valid for junction-pairs rather than a single probeset    
    if data_type == 'junctions':
        ### Re-import matches from above and export matching and non-matching transcripts for each probeset to a new file
        import_dir = '/AltDatabase/'+species+'/SequenceData/output'
        g = GrabFiles(); g.setdirectory(import_dir)
        align_files = g.searchdirectory('mRNA_alignments')
        reAnalyzeRNAProbesetMatches(align_files,species,array_type,pairwise_probeset_combinations)

if __name__ == '__main__':
    a = 'AltMouse'; b = 'exon'; array_type = a; force = 'no'
    h = 'Hs'; m = 'Mm'; species = m
    alignProbesetsToTranscripts(species,array_type,force)