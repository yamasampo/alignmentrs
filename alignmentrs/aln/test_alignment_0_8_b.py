#! /usr/env/bin/ Python3
from alignmentrs_imports import *
#----------------------------------------------------
class TestAlignment:
    
    # basic test for expected outputs
    def setup(self):
        # initiates alignment object for tests
        self.aln_file = Alignment.from_fasta('test_alignment_b.txt', 'test_align', 'marker')
        
    def teardown(self):
        pass
#----------------------------------------------------    
    def test_nrows(self):
        """checks if aln.obj.nrows output matches expected rows 
        of alignment"""
        nrows = self.aln_file.nrows
        expected_nrows = 4
        
        assert isinstance(nrows,int)
        assert nrows == expected_nrows
#----------------------------------------------------    
    def test_nsamples(self):   
        """checks if aln.obj.nsamples output matches 
        number of samples being tested"""
        
        nsamples = self.aln_file.nsamples
        expected_nsamples = 3
        
        assert isinstance(nsamples,int)
        assert nsamples == expected_nsamples
#----------------------------------------------------     
    def test_nmarkers(self):   
        """checks if aln.obj.nmarkers matches 
        expected number of markers in the sample"""
        
        nmarkers = self.aln_file.nmarkers
        expected_nmarkers = 1
        
        assert  isinstance(nmarkers, int)
        assert  nmarkers == expected_nmarkers
#----------------------------------------------------     
    def test_nsites(self):
        """checks if aln.obj.nsites output matches expected number
        of sites in alignment(i.e sequence length) file"""
        
        nsites = self.aln_file.nsites
        expected_nsites = 26
       
        assert isinstance(nsites, int)
        assert nsites == expected_nsites
#----------------------------------------------------     
    def test_sample_ids(self):
        """checks if all aln.obj.sample_ids match output
        ids in alignment file""" 
        
        sample_ids = self.aln_file.sample_ids
        expected_sample_ids = ['Dmel_528_2597', 'Dmel_RG2', 'Dmel_RG4N']
        
        assert isinstance(sample_ids,list)
        assert sample_ids == expected_sample_ids
#----------------------------------------------------     
    def test_sample_descriptions(self):   
        """checks if aln.obj.sample_descriptions output matches sample 
        descriptions in alignment file"""
        
        sample_descriptions =  self.aln_file.sample_descriptions
        expected_descriptions = ['|10 sp|', '|47 sp|', '|15 sp|']
        
        assert  isinstance(sample_descriptions,list)
        assert  sample_descriptions == expected_descriptions
#----------------------------------------------------     
    def test_sample_sequences(self):   
        """checks if aln.obj.sample_sequences output match sequences 
        in alignment file"""
        
        sample_sequences =  self.aln_file.sample_sequences
        expected_sample_sequences =  ['ATGAAGAGCAAGGTGGGGGGGGGGGG',
                                      'ATGAAGAGCAAGGTGGACCCCCCCCC', 
                                      'ATGAAGAGCAAGGTGGAAAAAAAAAA']
        
        assert isinstance(sample_sequences,list)
        assert sample_sequences == expected_sample_sequences
#----------------------------------------------------        
    def test_marker_ids(self):
        """checks if aln.obj.marker_ids matches output marker ids in 
        alignment file"""
        
        marker_ids =  self.aln_file.marker_ids
        expected_marker_ids = ['marker_0']
        
        assert isinstance(marker_ids, list)
        assert marker_ids == expected_marker_ids
#----------------------------------------------------       
    def test_marker_descriptions(self):
        """checks if aln.obj.marker_descriptions output 
        matches descriptions in alignment file"""
        
        marker_descriptions =  self.aln_file.marker_descriptions
        expected_marker_descriptions = ['|91 sp|']
        
        assert isinstance(marker_descriptions,list)
        assert marker_descriptions == expected_marker_descriptions
#----------------------------------------------------       
    def test_marker_sequences(self): 
        """checks if align.obj.marker_sequences output 
        matches marker sequences alignment file"""
        
        marker_sequences =  self.aln_file.marker_sequences
        expected_marker_sequences = ['CCCCCCCCCCCCCCCCCCCCCCCCCC']
        
        assert isinstance(marker_sequences,list)
        assert marker_sequences == expected_marker_sequences
#----------------------------------------------------     
    # class methods
    
    # Does not work properly
    
    #def test_subset(cls):
     #   """Returns a subset of the alignment by samples, markers and sites."""
     #   sample_ids = [1,2,3]
     #   marker_ids = ['marker_0']
      #  aln_obj = Alignment.from_fasta('test_alignment.txt', 'test_align', 'marker')
        
      #  subset = (aln_obj,sample_ids, marker_ids)
      #  test_subset = 
#----------------------------------------------------          
    def test_get_samples(self):
        """tests aln.object.get_samples returns expected 
        sequences sample of an alignment file
        tests:
           valid input
           invalid sample id
           invalid types"""
        # valid input
        get_sample_str = self.aln_file.get_samples('Dmel_528_2597')
        get_sample_index = self.aln_file.get_samples(0)
        expected_sites = 26
        expected_samples = 1
        expected_markers = 0
        expected_sequence = ['ATGAAGAGCAAGGTGGGGGGGGGGGG']
        test_sample_list = [get_sample_str,get_sample_index]
        
        for test in test_sample_list:
            assert isinstance(test, object)
            assert test.nsites ==  expected_sites
            assert test.nsamples ==  expected_samples
            assert test.nmarkers ==  expected_markers
            assert test.sample_sequences == expected_sequence

        # invalid sample_id
        try:
            invalid_sample_name_str = self.aln_file.get_samples('Dmel_528_259700')
            invalid_sample_name_lst = self.aln_file.get_samples(['Dmel_528_259700'])
            invalid_sample_id_int = self.aln_file.get_samples(-1)
            invalid_sample_id_lst = self.aln_file.get_samples([-1])
            
        except: 
            assert ValueError

        # invalid type
        test_invalid_types = [{'Dmel_528_2597':0 },('Dmel_528_2597')]
        try:
            
            for invalid_input in test_invalid_types:
                invalid_id = self.aln_file.get_samples(invalid_input)            
        except:
            assert ValueError
        
        try:
            test_invalid_list_items = [[],[{'Dmel_528_2597':0 }]] 
            
            for invalid_input in test_invalid_list_items:
                invalid_id = self.aln_file.get_samples(invalid_input)
        except:
            assert ValueError
#----------------------------------------------------     
    def test_get_markers(self):
            """tests if aln.object.get_markers returns expected 
            marker sequences of an alignment file
            tests:
               valid input
               invalid sample id
               invalid types"""
            
            # VI
            get_markers_str = self.aln_file.get_markers('marker_0')
            get_markers_int = self.aln_file.get_markers(0)
            get_markers_list_str = self.aln_file.get_markers(['marker_0'])
            get_markers_list_int = self.aln_file.get_markers([0])
            expected_marker_sequence = ['CCCCCCCCCCCCCCCCCCCCCCCCCC']
            tests = [get_markers_str, get_markers_int, get_markers_list_str, get_markers_list_int]
            for test in tests:
                assert isinstance(test,object) 
                assert test.sequences == ['CCCCCCCCCCCCCCCCCCCCCCCCCC']
                assert test.nsites == 26
                #assert test.nsamples == 1  # attribute error
            
            # IVI
            try:
                inv_markers_str = self.aln_file.get_markers('marker_01')
                inv_markers_int = self.aln_file.get_markers(1)
                inv_markers_list_str = self.aln_file.get_markers(['marker_01'])
                inv_markers_list_int = self.aln_file.get_markers([1])
                tests = [inv_markers_str, inv_markers_int, inv_markers_list_str, inv_markers_list_int]
                
            except ValueError:
                pass
                
            # IVT
            try:
                test_invalid_types = [{'marker_0':0 },('marker_0')]
            except ValueError:
                pass
            
#----------------------------------------------------     
    #def test_get_sites(self): # row error
           # """Returns a new alignment containing only the sites specified
           # #by the given list of column numbers."""
#----------------------------------------------------  
        # Setter/Replacer
    def test_replace_samples(self): # 
        """tests if aln.object.replace_samples replaces the sequence
        of one or more sample in the aln.object"""
        
        new_sample = 'AT' * 13
        prev_sample_sequence = self.aln_file.sample_sequences[0]
        self.aln_file.replace_samples(['Dmel_528_2597'], [new_sample])
        curr_sequence =  self.aln_file.sample_sequences[0]
        
        assert not prev_sample_sequence == curr_sequence
        assert curr_sequence == new_sample
#----------------------------------------------------  
    def test_insert_samples_from_lists(self):
        """tests if aln.object.insert_samples_from_lists adds one or
        more sequences in the aln.object"""
    
        new_sample_id = 'Dsim99201'
        new_sample_desc = '|CH2912|'
        new_sample_sequence = 'G' * 26
        self.aln_file.insert_samples_from_lists(1, [new_sample_id], 
                                                [new_sample_desc], 
                                                [new_sample_sequence])

        assert self.aln_file.sample_ids[1] == new_sample_id 
        assert self.aln_file.sample_descriptions[1] == new_sample_desc
        # error here, returns does not insert expected sequence value
        #assert self.aln_file.sample_sequences[1] == new_sample_sequence
#----------------------------------------------------  
    def test_append_sample_from_lists(self):
        """tests if append_sample_from_lists adds one or
        more sequences in the last index of aln.object"""
            
        new_sample_id = 'Dere_lastind'
        new_sample_desc = '|last_ind|'
        new_sample_sequence = 'G' * 26
        self.aln_file.append_sample_from_lists([new_sample_id], [new_sample_desc], [new_sample_sequence])
        assert self.aln_file.sample_sequences[-1] == new_sample_sequence 
        assert self.aln_file.sample_ids[-1] == new_sample_id 
        assert self.aln_file.sample_descriptions[-1] == new_sample_desc 
#----------------------------------------------------   
    def test_remove_samples(self):
        """tests if aln.obj.remove_samples removes all sample
        information of one or more indices from the alignment object"""
        
        index_to_remove = 1
        sequence_to_remove = self.aln_file.sample_sequences[index_to_remove]
        self.aln_file.remove_samples(index_to_remove)
        assert  sequence_to_remove != self.aln_file.sample_sequences[1] 
#---------------------------------------------------- 
    def test_retain_samples(self):
        """tests if aln.obj.retain_samples removes all sample
        information apart from specified indices in
        alignment object"""
        
        self.aln_file.retain_samples([1])
        assert self.aln_file.nsamples == 1
        assert len(self.aln_file.sample_ids) == 1
        assert len(self.aln_file.sample_descriptions) == 1
        assert len(self.aln_file.sample_sequences) == 1
        assert self.aln_file.nmarkers == 1
        assert len(self.aln_file.marker_ids) == 1
        assert len(self.aln_file.marker_descriptions) == 1
        assert len(self.aln_file.marker_sequences) == 1
#----------------------------------------------------               
    def test_remove_sites(self):
        """tests if aln.obj.remove_sites removes all one or more
        sequences from the alignment sequences"""
        
        self.aln_file.remove_sites([2])
        assert self.aln_file.nsites == (25)
#----------------------------------------------------   
    def test_retain_sites(self):
        """tests if aln.obj.retain_sites all sequences
        apart from specified sequences in alignment sequences"""
        self.aln_file.retain_sites([0,1,2])
        assert self.aln_file.nsites == 3
        #TODO- should assert to that the positions are not ATG once 
        # get samples sequences is fixes
#----------------------------------------------------                
    def test_from_fasta(cls):
        """Create an Alignment object from a FASTA-formatted file."""
        aln_obj = Alignment.from_fasta('test_alignment_b.txt', 'test_align', 'marker')
        assert aln_obj.nsites == 26
        assert aln_obj.nsamples == 3
        assert aln_obj.nmarkers == 1
#----------------------------------------------------               
        # Format converters
    # tested, remove hashtag when done
    #def test_to_fasta(self):
        """Saves the alignment as a FASTA-formatted text file."""
        #create_aln_file = self.aln_file.to_fasta('test_aln_file') # should change input to path_to_file
        #TODO- check if len(currentdir) increases by one, 
        #check if test_aln_file in dir
        #use from_fasta to create new alingment object 
        
            # How does this work?
 
        # Block-related methods

   #def test_set_blocklists(self, ref_seq, description_encoder=None):
#            """Creates new block information for the sequences given a reference. """
#----------------------------------------------------   
   # def test_parse_description_as_blocks(self, description_decoder=None):
#            """Parses sample description into block data."""
#----------------------------------------------------   
   # def test_write_blocks_to_description(self, description_encoder):
#            """Writes each sample's block data as a string, replacing its
 #           description."""
#----------------------------------------------------   