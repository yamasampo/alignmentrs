use pyo3::prelude::*;
use pyo3::{PyObjectProtocol, exceptions};


#[pyclass(subclass)]
#[derive(Clone)]
/// Block(id, start, stop)
/// 
/// Block represents a linear interval.
pub struct Block {

    #[prop(get,set)]
    pub id: String,

    #[prop(get,set)]
    pub start: i32,
    
    #[prop(get,set)]
    pub stop: i32,

}

#[pymethods]
impl Block {
    #[new]
    /// Creates a new Block object from an id, and start and stop
    /// coordinates.
    fn __new__(obj: &PyRawObject, id: &str, start: i32, stop: i32) -> PyResult<()> {
        if start > stop {
            return Err(exceptions::ValueError::py_err(
                format!("start must be less than stop: {} !< {}",
                        start, stop)))
        }
        obj.init(|_| {
            let id = id.to_string();
            Block { id, start, stop }
        })
    }

    /// in_block(i)
    /// 
    /// Returns True if a given position is inside the block.
    /// Otherwise, returns False.
    fn in_block(&self, i: i32) -> PyResult<bool> {
        if i >= self.start && i < self.stop {
            return Ok(true)
        }
        Ok(false)
    }

    /// to_array()
    ///
    /// Converts the block into a list of positions.
    fn to_array(&self) -> PyResult<Vec<i32>> {
        Ok(self._to_array())
    }

    // Formatting methods

    /// to_compressed_str()
    ///
    /// Converts block into a compressed string representation.
    fn to_compressed_str(&self) -> PyResult<String> {
        self.__str__()
    }

    /// to_extended_str()
    ///
    /// Converts block into an extended (human-readable) string
    /// representation.
    fn to_extended_str(&self) -> PyResult<String> {
        Ok(format!("{}={}:{}", self.id, self.start, self.stop))
    }
    
    // TODO: Add a method to convert to CIGAR string
    // fn to_cigar_str(&self) -> PyResult<String> {
    // }

    /// to_array_str()
    /// 
    /// Converts block into comma-separated list of positions.
    fn to_array_str(&self) -> PyResult<String> {
        let v: Vec<String> = self._to_array().iter()
                                .map(|x| format!("{}", x))
                                .collect();
        Ok(v.join(","))
    }
}

impl Block {
    fn _to_array(&self) -> Vec<i32> {
        (self.start..self.stop).collect::<Vec<i32>>()
    }
}

#[pyproto]
impl PyObjectProtocol for Block {
    fn __repr__(&self) -> PyResult<String> {
        Ok(format!("Block(id=\"{}\", start={}, stop={}",
                   self.id, self.start, self.stop))
    }
    
    fn __str__(&self) -> PyResult<String> {
        Ok(format!("{}{}{}", self.start, self.id, self.stop))
    }
}

#[pyclass(subclass)]
#[derive(Clone)]
/// LinearSpace(init_state, start, stop)
/// 
/// LinearSpace represents a discrete linear space stored
/// in intervals called Blocks.
pub struct LinearSpace {

    coords: Vec<(i32, i32, String)>,

}

#[pyproto]
impl PyObjectProtocol for LinearSpace {
    fn __repr__(&self) -> PyResult<String> {
        let lb = match self.lb() {
            Ok(x) => x,
            Err(x) => return Err(x)
        };
        let ub = match self.ub() {
            Ok(x) => x,
            Err(x) => return Err(x)
        };
        let length = match self.len() {
            Ok(x) => x,
            Err(x) => return Err(x)
        };
        Ok(format!("LinearSpace(lb={}, ub={}, length={})", lb, ub, length))
    }
    
    fn __str__(&self) -> PyResult<String> {
        let mut strings: Vec<String> = Vec::new();
        if let Ok(blocks) = self.to_blocks() {
            for block in blocks {
                if let Ok(s) = block.__str__() {
                    strings.push(s);
                } else {
                    return Err(exceptions::ValueError::py_err("cannot get string representation of block"))
                }
            }
        } else {
            return Err(exceptions::ValueError::py_err("cannot generate blocks"))
        }
        Ok(strings.join(","))
    }
}

#[pymethods]
impl LinearSpace {
    #[new]
    /// Creates a new LinearSpace object from an init_state, and start and stop
    /// coordinates.
    fn __new__(obj: &PyRawObject, start: i32, stop: i32, init_state: &str) -> PyResult<()> {
        if start > stop {
            return Err(exceptions::ValueError::py_err(
                format!("start must be less than stop: {} !< {}",
                        start, stop)))
        }
        obj.init(|_| {
            LinearSpace {
                coords: vec![(start, stop, init_state.to_string())],
            }
        })
    }

    // Add extract function for "get"
    // fn extract(&self, coords: Vec<i32>) ->PyResult<LinearSpace> {
    // }
    fn remove(&mut self, positions: Vec<i32>) -> PyResult<()> {
        match self._remove(positions) {
            Ok(_) => Ok(()),
            Err(msg) => Err(exceptions::IndexError::py_err(msg.to_string()))
        }
    }

    fn retain(&mut self, positions: Vec<i32>) -> PyResult<()> {
        match self._retain(positions) {
            Ok(_) => Ok(()),
            Err(msg) => Err(exceptions::IndexError::py_err(msg.to_string()))
        }
    }

    // start, stop, full_len

    /// Returns the lower bound of the linear space.
    fn lb(&self) -> PyResult<i32> {
        match self._lb() {
            Ok(v) => Ok(v),
            Err(msg) => Err(exceptions::ValueError::py_err(msg.to_string()))
        }
    }

    /// Returns the upper bound of the linear space.
    /// This value is not part of the space.
    fn ub(&self) -> PyResult<i32> {
        match self._ub() {
            Ok(v) => Ok(v),
            Err(msg) => Err(exceptions::ValueError::py_err(msg.to_string()))
        }
    }

    /// Returns the total length of the linear space.
    fn len(&self) -> PyResult<i32> {
        Ok(self._len())
    }
    
    // Format conversion

    /// Returns the linear space as a list of blocks.
    fn to_blocks(&self) -> PyResult<Vec<Block>> {
        match self._to_blocks() {
            Ok(v) => Ok(v),
            Err(msg) => Err(exceptions::IndexError::py_err(msg.to_string()))
        }
    }

    /// Returns the linear space as a list of integer coordinates.
    fn to_list(&self) -> PyResult<Vec<(i32, i32, String)>> {
        match self._to_list() {
            Ok(coords) => {
                let mut list: Vec<(i32, i32, String)> = Vec::new();
                for (start, stop, id) in coords.iter() {
                    list.push((*start, *stop, id.clone()));
                }
                Ok(list)
            },
            Err(msg) => Err(exceptions::IndexError::py_err(msg.to_string()))
        }
    }

    // Formatting methods

    /// Converts block into a compressed string representation.
    fn to_compressed_str(&self) -> PyResult<String> {
        Ok(self._to_compressed_str())
    }

    /// Converts block into an extended (human-readable) string
    /// representation.
    fn to_extended_str(&self) -> PyResult<String> {
        Ok(self._to_extended_str())
    }

    /// Converts block into comma-separated list of positions.
    fn to_array_str(&self) -> PyResult<String> {
        Ok(self._to_array_str())        
    }

    /// Returns a deep copy of the current linear space.
    fn copy(&self) -> PyResult<LinearSpace> {
        Ok(self._copy())
    }
}

impl LinearSpace {
    fn _remove(&mut self, positions: Vec<i32>) -> Result<(), &str> {
        // Check if positions list is empty or not using max()
        if let Some(max) = positions.iter().max() {
            // If largest relative position is larger than the total length
            // of the linear space, then return an error
            if *max >= self._len() {
                return Err("index out of range")
            }
            // Create a vector of arrays representing relative start and stops
            let mut start_offset = 0;
            let rel_blocks: Vec<[i32;2]> = self.coords.iter().map(|(a, z, _)| 
            {
                let length = z - a;
                start_offset += length;
                [start_offset-length, start_offset]
            }).collect();
            // Sort positions in reverse order
            let mut positions = positions;
            positions.sort_unstable();
            positions.reverse();
            let mut offset = 0;
            for &rel_pos in positions.iter() {
                let length = rel_blocks.len() - offset;
                for i in (0..length).rev() {
                    let [rel_start, rel_stop]: [i32; 2] = rel_blocks[i];
                    let (abs_start, abs_stop, id) = self.coords[i];
                    if rel_pos > rel_start && rel_pos < rel_stop - 1 {
                        // Remove block currently at j and get values
                        // Split this block at pos
                        // 10,11,12,13,14,15 : remove at index 2 (3rd pos)
                        // [_,10,16]
                        // 10,11,   13,14,15
                        // [_,10,12], [13:16]
                        // Insert two new blocks at j and j+1
                        let abs_pos = abs_start + (rel_pos - rel_start);
                        self.coords[i] = (abs_start, abs_pos, id);
                        self.coords.insert(i+1, (abs_pos+1, abs_stop, id));
                        offset += 1;
                        break;
                    } else if rel_pos == rel_start {
                        if abs_start+1 == abs_stop {
                            let _ = self.coords.remove(i);
                            // no offset increment
                        } else {
                            self.coords[i] = (abs_start+1, abs_stop, id);
                            offset += 1;
                        }
                        break;
                    } else if rel_pos == rel_stop - 1 {
                        self.coords[i] = (abs_start, abs_stop-1, id);
                        // no offset increment
                        break;
                    }
                }
            }
        } 
        Ok(())
    }

    fn _retain(&mut self, positions: Vec<i32>) -> Result<(), &str> {
        // Check if positions list is empty or not using max()
        if let Some(max) = positions.iter().max() {
            // If largest relative position is larger than the total length
            // of the linear space, then return an error
            if *max >= self._len() {
                return Err("index out of range")
            }
            let inverse_rel_positions: Vec<i32> = (0..self._len())
                .filter(|x| !positions.contains(x))
                .collect();
            return self._remove(inverse_rel_positions)
        } 
        Ok(())
    }

    // fn insert(&mut self, pos: i32, state: i32, length: i32) -> PyResult<()> {
    //     Ok(())
    // }

    // These methods relies on reading into the block
    // But another way to access it is the relative position of the block

    // /// Removes points in linear space given based on a list of coordinates.
    // fn _remove_abs(&mut self, positions: Vec<i32>) -> PyResult<()> {
    //     let mut positions = positions;
    //     positions.sort_unstable();
    //     positions.reverse();
    //     let mut offset = 0;
    //     for &pos in positions.iter() {
    //         let length = self.coords.len() - offset;
    //         for i in (0..length).rev() {
    //             let [start, stop, id]: [i32; 3] = self.coords[i];
    //             if pos > start && pos < stop - 1 {
    //                 // Remove block currently at j and get values
    //                 // Split this block at pos
    //                 // 10,11,12,13,14,15 : remove at index 2 (3rd pos)
    //                 // [_,10,16]
    //                 // 10,11,   13,14,15
    //                 // [_,10,12], [13:16]
    //                 // Insert two new blocks at j and j+1
    //                 self.coords[i] = [start, pos, id];
    //                 self.coords.insert(i+1, [pos+1, stop, id]);
    //                 offset += 1;
    //             } else if pos == start {
    //                 if start == stop - 1 {
    //                     let _ = self.coords.remove(i);
    //                     // no offset increment
    //                 } else {
    //                     self.coords[i] = [pos+1, stop, id];
    //                     // no offset increment
    //                 }
    //             } else if pos == stop - 1 {
    //                 self.coords[i] = [start, pos, id];
    //                 // no offset increment
    //             }
    //         }
    //     }
    //     Ok(())
    // }

    // /// Retains points in linear space specified by a
    // /// list of coordinates to keep.
    // fn _retain_abs(&mut self, coords: Vec<i32>) -> PyResult<()> {
    //     if let Some([_, _, stop]) = self.coords.last() {
    //         let inverse_ilist: Vec<i32> = (0..*stop)
    //                                         .filter(|x| !coords.contains(x))
    //                                         .collect();
    //         return self.remove(inverse_ilist)
    //     };
    //     Err(exceptions::ValueError::py_err("cannot perform retain on \
    //                                         dimension: block list is empty"))
    // }

    // /// Inserts into the linear space at the given position.
    // fn _insert_abs(&mut self, pos: i32, state: i32, length: i32) -> PyResult<()> {
    //     for i in 0..self.coords.len() {
    //         let [id, start, stop] = self.coords[i];
    //         if start >= pos && stop < pos {
    //             if id == state {
    //                 // Extend current block
    //                 self.coords[i] = [id, start, stop + length];
    //             } else {
    //                 // Create new state
    //                 self.coords.insert(i + 1, [id, stop, stop + length]);
    //             }
    //             // Adjust
    //             for j in i..self.coords.len() {
    //                 let [id, start, stop] = self.coords[j];
    //                 self.coords[j] = [id, start+length, stop+length];
    //             }
    //             break;
    //         }
    //     }
    //     Ok(())
    // }

    // /// Appends to the end of the linear space.
    // fn _append_abs(&mut self, state: i32, length: i32) -> PyResult<()> {
    //     if let Some([id, start, stop]) = self.coords.last() {
    //         let (id, start, stop) = (*id, *start, *stop);
    //         let i = self.coords.len();
    //         if id == state {
    //             // Extend current block
    //             self.coords[i] = [id, start, stop + length];
    //         } else {
    //             // Create new state
    //             self.coords.push([id, stop, stop + length]);
    //         }
    //     } else {
    //         self.coords.push([state, 0, length]);
    //     }
    //     Ok(())
    // }

    // start, stop, full_len

    /// Returns the lower bound of the linear space.
    fn _lb(&self) -> Result<i32, &str> {
        match self.coords.first() {
            Some((x, _, _)) => Ok(*x),
            None => Err("linear space is empty")
        }
    }

    /// Returns the upper bound of the linear space.
    /// This value is not part of the space.
    fn _ub(&self) -> Result<i32, &str> {
        match self.coords.last() {
            Some((_, x, _)) => Ok(*x),
            None => Err("linear space is empty")
        }
    }

    /// Returns the total length of the linear space.
    fn _len(&self) -> i32 {
        let mut length = 0;
        for &(start, stop, _) in self.coords.iter() {
            length += stop - start;
        }
        length
    }
    
    // Format conversion

    
    /// Returns the linear space as a list of blocks.
    fn _to_blocks(&self) -> Result<Vec<Block>, &str> {
        let mut blocks: Vec<Block> = Vec::new();
        for (start, stop, id) in self.coords.iter() {
            blocks.push(Block{ id: id.clone(), start: *start, stop: *stop });
        }
        Ok(blocks)
    }

    /// Returns the linear space as a list of integer coordinates.
    fn _to_list(&self) -> Result<Vec<(i32, i32, String)>, &str> {
        Ok(self.coords.clone())
    }

    // Formatting methods

    /// Converts block into a compressed string representation.
    fn _to_compressed_str(&self) -> String {
        let mut strings: Vec<String> = Vec::new();
        for (start, stop, id) in self.coords.iter() {
            strings.push(format!("{}={}", id, stop-start));
        }
        strings.join(";")
    }

    /// Converts block into an extended (human-readable) string
    /// representation.
    fn _to_extended_str(&self) -> String {
        let mut strings: Vec<String> = Vec::new();
        for (start, stop, id) in self.coords.iter() {
            strings.push(format!("{}={}:{}", id, start, stop));
        }
        strings.join(";")
    }

    /// Converts block into comma-separated list of positions.
    fn _to_array_str(&self) -> String {
        let mut strings: Vec<String> = Vec::new();
        for (start, stop, id) in self.coords.iter() {
            let mut b_strings: Vec<String> = Vec::new();
            b_strings.push(format!("{}=", id));
            for i in *start..*stop {
                b_strings.push(format!("{}", i));
            }
            strings.push(b_strings.join(","));
        }
        strings.join(";")
    }

    /// Returns a deep copy of the current linear space.
    fn _copy(&self) -> LinearSpace {
        let coords = self.coords.clone();
        LinearSpace{ coords }
    }
}

fn _list_to_linspace<'a>(coords: Vec<(i32, i32, String)>) -> Result<LinearSpace, &'a str> {
    let coords: Vec<(i32, i32, String)> = coords.iter().map(|(a, b, c)| (*a, *b, c.clone())).collect();
    Ok(LinearSpace{ coords })
}

/// Returns a linear space created using the given coordinate list.
fn list_to_linspace(coords: Vec<(i32, i32, String)>) -> PyResult<LinearSpace> {
    match _list_to_linspace(coords) {
        Ok(v) => Ok(v),
        Err(msg) => Err(exceptions::ValueError::py_err(msg.to_string()))
    }
}

fn _blocks_to_linspace<'a>(blocks: Vec<&Block>) -> Result<LinearSpace, &'a str> {
    let mut coords: Vec<(i32, i32, String)> = Vec::new();
    for Block{ id, start, stop } in blocks.iter() {
        coords.push((*start, *stop, id.clone()));
    }
    Ok(LinearSpace{ coords })
}

/// Returns a linear space created using the given list of blocks.
fn blocks_to_linspace(blocks: Vec<&Block>) -> PyResult<LinearSpace> {
    match _blocks_to_linspace(blocks) {
        Ok(v) => Ok(v),
        Err(msg) => Err(exceptions::ValueError::py_err(msg.to_string()))
    }
}


#[pyclass(subclass)]
#[derive(Clone)]
/// CoordSpace(init_state, start, stop)
/// 
/// CoordSpace represents a discrete linear space stored as a 
/// list of integer coordinates.
pub struct CoordSpace {

    coords: Vec<i32>

}

#[pymethods]
impl CoordSpace {
    #[new]
    /// Creates a new CoordSpace object from an init_state, and start and stop
    /// coordinates.
    fn __new__(obj: &PyRawObject, start: i32, stop: i32) -> PyResult<()> {
        if start > stop {
            return Err(exceptions::ValueError::py_err(
                format!("start must be less than stop: {} !< {}",
                        start, stop)))
        }
        obj.init(|_| {
            CoordSpace { 
                coords: (start..stop).collect(),
            }
        })
    }

    /// extract(coordinates)
    /// 
    /// Extracts coordinates by relative positions as a new CoordSpace.
    fn extract(&self, coords: Vec<i32>) -> PyResult<CoordSpace> {
        if let Some(max) = coords.iter().max() {
            if *max >= self.coords.len() as i32 {
                return Err(exceptions::IndexError::py_err(format!("index out of range: {}", max)))
            }
            let mut new_coords: Vec<i32> = Vec::new();
            for i in coords.iter() {
                new_coords.push(self.coords[*i as usize]);
            }
            Ok(CoordSpace{ coords: new_coords })
        } else {
            Ok(CoordSpace { coords: self.coords.clone()})
        }
    }

    /// remove(coordinates)
    /// 
    /// Removes points in linear space given based on a list of relative
    /// coordinates.
    fn remove(&mut self, coords: Vec<i32>) -> PyResult<()> {
        if let Some(max) = coords.iter().max() {
            if *max >= self.coords.len() as i32 {
                return Err(exceptions::IndexError::py_err(format!("index out of range: {}", max)))
            }
            self.coords = self.coords.iter().enumerate().filter(|(i, _)| !coords.contains(&(*i as i32))).map(|(_, x)| *x ).collect();
            Ok(())
        } else {
            Ok(())
        }
        
    }

    /// retain(coordinates)
    /// 
    /// Retains points in linear space specified by a
    /// list of coordinates to keep.
    fn retain(&mut self, coords: Vec<i32>) -> PyResult<()> {
        if let Some(max) = coords.iter().max() {
            if *max >= self.coords.len() as i32 {
                return Err(exceptions::IndexError::py_err(format!("index out of range: {}", max)))
            }
            self.coords = self.coords.iter().enumerate().filter(|(i, _)| coords.contains(&(*i as i32))).map(|(_, x)| *x ).collect();
            Ok(())
        } else {
            self.coords = Vec::new();
            Ok(())
        }        
    }

    // /// Inserts into the linear space at the given position.
    // fn insert(&mut self, pos: i32, start: i32, length: i32) -> PyResult<()> {
    //     // Insert to start of list if pos is 0,
    //     // Append to end of list if pos is the length,
    //     // Otherwise split at the position and concat
    //     if pos == 0 {
    //         let mut new_coords: Vec<i32> = (start..start+length).collect();
    //         new_coords.append(&mut self.coords);
    //         self.coords = new_coords;
    //         return Ok(())
    //     } else if pos == self.coords.len() as i32 {
    //         return self.append(start, length)
    //     } // TODO: else if pos > self.coords.len()
    //     // Split list into two and combine
    //     let mut new_coords: Vec<i32> = (start..start+length).collect();
    //     let (left, right) = self.coords.split_at(pos as usize);
    //     let mut left: Vec<i32> = left.iter().map(|x| *x ).collect();
    //     let mut right: Vec<i32> = right.iter().map(|x| *x ).collect();
    //     left.append(&mut new_coords);
    //     left.append(&mut right);
    //     self.coords = left;
    //     Ok(())
    // }

    // /// Appends to the end of the linear space.
    // fn append(&mut self, start: i32, length: i32) -> PyResult<()> {
    //     let mut new_coords: Vec<i32> = (start..start+length).collect();
    //     self.coords.append(&mut new_coords);
    //     Ok(())
    // }

    // start, stop, full_len

    /// start()
    /// 
    /// Returns the value at the start of the linear space.
    fn start(&self) -> PyResult<i32> {
        Ok(self.coords[0])
    }

    /// stop()
    /// 
    /// Returns the end value of the linear space.
    /// This value is not part of the space.
    fn stop(&self) -> PyResult<i32> {
        if self.coords.len() > 0 {
            Ok(self.coords[self.coords.len() - 1])
        } else {
            Ok(0)
        }
    }

    /// len_all()
    /// 
    /// Returns the total length of the linear space.
    fn len_all(&self) -> PyResult<i32> {
        Ok(self.coords.len() as i32)
    }

    /// len_seq()
    /// 
    /// Returns the total length of the linear space where the
    /// state is equal to 1.
    fn len_seq(&self) -> PyResult<i32> {
        let length = self.coords.iter().filter(|x| **x > 0).collect::<Vec<&i32>>().len();
        Ok(length as i32)
    }

    /// len_gap()
    /// 
    /// Returns the total length of the linear space where the
    /// state is equal to 0.
    fn len_gap(&self) -> PyResult<i32> {
        let length = self.coords.iter().filter(|x| **x < 0).collect::<Vec<&i32>>().len();
        Ok(length as i32)
    }
    
    // Format conversion

    #[staticmethod]
    /// from_blocks(blocks)
    /// 
    /// Returns a linear space created using the given list of blocks.
    fn from_blocks(blocks: Vec<&Block>) -> PyResult<CoordSpace> {
        if blocks.len() == 0 {
            let coords: Vec<i32> = Vec::new();
            return Ok(CoordSpace{ coords })
        }
        match blocks_to_arrays(blocks) {
            Ok((data, ids)) => {
                let mut new_data: Vec<i32> = Vec::new();
                for i in 0..data.len() {
                    let x = data[i];
                    let id = &ids[i];
                    if id == "s" {
                        new_data.push(x);
                    } else if id == "g" {
                        new_data.push(-1);
                    } else {
                        return Err(exceptions::ValueError::py_err(format!("unsupported ID: {}. Use \"s\" for sequence or \"g\" for gap.", id)))
                    }
                }
                Ok(CoordSpace { coords: new_data })
            },
            Err(x) => return Err(x)
        }
        
    }

    #[staticmethod]
    /// from_arrays(coordinates, ids)
    /// 
    /// Returns a linear space created using the corresponding lists of
    /// coordinates and ids.
    fn from_arrays(data: Vec<i32>, ids: Vec<String>) -> PyResult<CoordSpace> {
        if data.len() != ids.len() {
            return Err(exceptions::ValueError::py_err("lengths of data and ids do not match"))
        }
        if data.len() == 0 {
            let coords: Vec<i32> = Vec::new();
            return Ok(CoordSpace{ coords })
        }
        let mut coords: Vec<i32> = Vec::new();
        for i in 0..data.len() {
            let x = data[i];
            let id = &ids[i];
            if id == "s" {
                coords.push(x);
            } else if id == "g" {
                coords.push(-1);
            } else {
                return Err(exceptions::ValueError::py_err(format!("unsupported ID: {}. Use \"s\" for sequence or \"g\" for gap.", id)))
            }
        }
        Ok(CoordSpace{ coords })
    }

    /// to_blocks()
    /// 
    /// Returns the linear space as a list of blocks.
    fn to_blocks(&self) -> PyResult<Vec<Block>> {
        if self.coords.len() == 0 {
            return Ok(Vec::new())
        }
        // Declare variables
        let mut blocks: Vec<Block> = Vec::new();
        let mut last_start: i32 = self.coords[0];
        let mut last_id: String = match self.coords[0] {
            x if x >= 0 => "s".to_string(),
            x if x == -1 => "g".to_string(),
            x => return Err(exceptions::ValueError::py_err(format!("unexpected coordinate value: {}", x))),
        };
        let mut negative_length: i32 = 0;

        for i in 1..self.coords.len() {
            let c_id: String = match self.coords[0] {
                x if x >= 0 => "s".to_string(),
                x if x == -1 => "g".to_string(),
                x => return Err(exceptions::ValueError::py_err(format!("unexpected coordinate value: {}", x))),
            };
            let c_pos = self.coords[i];
            let p_pos = self.coords[i-1];

            if c_pos == -1 && p_pos == -1 {
                negative_length += 1;
            } else if c_pos < -1 || p_pos < -1 {
                // Return an error
                return Err(exceptions::ValueError::py_err(format!("unexpected coordinate value: {}", c_pos)))
            } else if c_pos == -1 && p_pos >= 0 {
                // Create new block and push
                blocks.push(Block{ id: last_id, start: last_start, stop: p_pos + 1});
                // Assign current id as last_id and current pos as last_start
                last_id = c_id;
                last_start = c_pos;
                negative_length = 0;
            } else if c_pos >= 0 && p_pos == -1 {
                // Create new block and push
                blocks.push(Block{ id: last_id, start: 0, stop: negative_length});
                // Assign current id as last_id and current pos as last_start
                last_id = c_id;
                last_start = c_pos;
                negative_length = 0;
            } else if c_pos >= 0 && p_pos >= 0 {
                if c_pos != p_pos + 1 {
                    // Create new block and push
                    blocks.push(Block{ id: last_id, start: last_start, stop: p_pos + 1});
                    // Assgin current id as last_id and current pos as last_start
                    last_id = c_id;
                    last_start = c_pos;
                }
            }
        }
        blocks.push(Block{ id: last_id, start: last_start, stop: self.coords.last().unwrap() + 1});
        Ok(blocks)
    }

    /// to_arrays()
    /// 
    /// Returns the linear space as a list of integer coordinates.
    fn to_arrays(&self) -> PyResult<(Vec<i32>, Vec<String>)> {
        let coords = self.coords.clone();
        let mut ids: Vec<String> = Vec::new();
        for coord in self.coords.iter() {
            if *coord >= 0 {
                ids.push("s".to_string());
            } else if *coord == -1 {
                ids.push("g".to_string())
            } else {
                return Err(exceptions::ValueError::py_err(format!("unexpected coordinate value: {}", coord)))
            }
        }
        Ok((coords, ids))
    }

    // Formatting methods

    /// to_compressed_str()
    /// 
    /// Converts block into a compressed string representation.
    fn to_compressed_str(&self) -> PyResult<String> {
        self.__str__()
    }

    /// to_extended_str()
    /// 
    /// Converts block into an extended (human-readable) string
    /// representation.
    fn to_extended_str(&self) -> PyResult<String> {
        let mut strings: Vec<String> = Vec::new();
        if let Ok(blocks) = self.to_blocks() {
            for block in blocks {
                if let Ok(s) = block.to_extended_str() {
                    strings.push(s);
                } else {
                    return Err(exceptions::ValueError::py_err("cannot get string representation of block"))
                }
            }
        } else {
            return Err(exceptions::ValueError::py_err("cannot generate blocks"))
        }
        Ok(strings.join(","))
    }

    /// to_array_str()
    /// 
    /// Converts block into comma-separated list of positions.
    fn to_array_str(&self) -> PyResult<String> {
        let mut strings: Vec<String> = Vec::new();
        if let Ok(blocks) = self.to_blocks() {
            for block in blocks {
                if let Ok(s) = block.to_array_str() {
                    strings.push(s);
                } else {
                    return Err(exceptions::ValueError::py_err("cannot get string representation of block"))
                }
            }
        } else {
            return Err(exceptions::ValueError::py_err("cannot generate blocks"))
        }
        Ok(strings.join(","))
    }

    /// copy()
    /// 
    /// Returns a deep copy of the current linear space.
    fn copy(&self) -> PyResult<CoordSpace> {
        let coords = self.coords.clone();
        Ok(CoordSpace{ coords })
    }

}

#[pyproto]
impl PyObjectProtocol for CoordSpace {
    fn __repr__(&self) -> PyResult<String> {
        let start = match self.start() {
            Ok(x) => x,
            Err(x) => return Err(x)
        };
        let stop = match self.stop() {
            Ok(x) => x,
            Err(x) => return Err(x)
        };
        let length = match self.len_all() {
            Ok(x) => x,
            Err(x) => return Err(x)
        };
        Ok(format!("CoordSpace(start={}, stop={}, length={})", start, stop, length))
    }
    
    fn __str__(&self) -> PyResult<String> {
        let mut strings: Vec<String> = Vec::new();
        match self.to_blocks() {
            Ok(blocks) => {
                for block in blocks {
                    if let Ok(s) = block.__str__() {
                        strings.push(s);
                    } else {
                        return Err(exceptions::ValueError::py_err("cannot get string representation of block"))
                    }
                }
            },
            Err(_) => {
                return Err(exceptions::ValueError::py_err(format!("cannot generate blocks")))
            }
            
        }
        Ok(strings.join(","))
    }
}


#[pyfunction]
/// blocks_to_arrays(block_list)
/// 
/// Converts a list of Blocks into an explicit listing of positions.
/// Returns a list of integers.
pub fn blocks_to_arrays(blocks: Vec<&Block>) -> PyResult<(Vec<i32>, Vec<String>)> {
    let mut data: Vec<i32> = Vec::new();
    let mut ids: Vec<String> = Vec::new();
    for Block{ id, start, stop} in blocks.iter() {
        let mut new_coords: Vec<i32> = (*start..*stop).collect();
        let mut new_ids: Vec<String> = vec![format!("{}", id); new_coords.len()];
        data.append(&mut new_coords);
        ids.append(&mut new_ids);
    }
    Ok((data, ids))
}

#[pyfunction]
/// arrays_to_blocks(data, ids)
/// 
/// Converts an explicit list of positions into a list of blocks.
/// Returns a list of Block objects.
pub fn arrays_to_blocks(data: Vec<i32>, ids: Vec<String>) -> PyResult<Vec<Block>> {
    if data.len() != ids.len() {
        return Err(exceptions::ValueError::py_err("lengths of data and ids do not match"))
    }
    if data.len() == 0 {
        return Ok(Vec::new())
    }
    // Declare variables
    let mut blocks: Vec<Block> = Vec::new();
    let mut last_id: &str = &ids[0];
    let mut last_start: i32 = data[0];

    for i in 1..data.len() {
        let c_id = &ids[i];
        let c_pos = data[i];
        let p_pos = data[i-1];
        // Scenarios:
        // 1a) current and last ids are the same, current +1 of previous
        // 1b) current and last ids are the same, current NOT +1 of previous
        // 2a) current and last ids NOT the same, current +1 of previous
        // 2b) current and last ids NOT the same, current NOT +1 of previous
        //
        // 2a and 2b are the same scenario, because change in ID should always
        // generate a new block
        if c_id == last_id {
            if c_pos != p_pos + 1 {
                // Create new block and push
                blocks.push(Block{ id: last_id.to_string(), start: last_start, stop: p_pos + 1});
                // Assgin current id as last_id and current pos as last_start
                last_id = c_id;
                last_start = c_pos;
            }
        } else {
            // Create new block and push
            blocks.push(Block{ id: last_id.to_string(), start: last_start, stop: p_pos + 1});
            // Assign current id as last_id and current pos as last_start
            last_id = c_id;
            last_start = c_pos;
        }
    }
    blocks.push(Block{ id: last_id.to_string(), start: last_start, stop: data.last().unwrap() + 1});
    Ok(blocks)
}

#[pymodinit]
fn position(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Block>()?;
    // m.add_class::<LinearSpace>()?;
    m.add_class::<CoordSpace>()?;

    Ok(())
}
