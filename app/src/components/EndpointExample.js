import React, {useState} from 'react';

import Container from 'react-bootstrap/Container';
import { TitleCard, DropdownSelector, StatusBox, OdinDoubleSlider } from 'odin-react';
import { WithEndpoint, useAdapterEndpoint, ToggleSwitch } from 'odin-react';
import Button from 'react-bootstrap/Button';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Dropdown from 'react-bootstrap/Dropdown'
import { InputGroup } from 'react-bootstrap';


const EndpointDropdown = WithEndpoint(DropdownSelector);
const EndpointButton = WithEndpoint(Button);
const EndpointInput = WithEndpoint(Form.Control);
const EndpointToggleButton = WithEndpoint(ToggleSwitch);
const EndpointDoubleSlider = WithEndpoint(OdinDoubleSlider);

const ENDPOINT_URL = "http://127.0.0.1:8888";


function EndpointExamplePage(props) {
    const {postPutMethod} = props;
    
    const staticEndpoint = useAdapterEndpoint("react", ENDPOINT_URL);
    //const periodicEndpoint = useAdapterEndpoint("react", ENDPOINT_URL, 1000);
    //console.log(periodicEndpoint)

    const [data, changeData] = useState(100);

    const onChangeData = (event) => {
        console.log(event);
        changeData(+event.target.value);
    }

    const onSliderChange = (event) => {
        console.log(event);
    }

    const prePutMethod = (message) => {
        console.log("Pre Message: %s", message);
    }

    return
}

export default EndpointExamplePage;